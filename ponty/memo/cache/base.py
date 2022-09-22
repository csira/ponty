import abc
from contextlib import asynccontextmanager
import functools
import hashlib
import json
import typing
import warnings

from ponty.memo.lock.base import Lock, Locked
from ponty.registry import Registry


class Stampede(Locked):
    """Raised when the cache comes under high load and the lock times out.

    Inherits :class:`Locked <ponty.memo.Locked>`.

    """


class cachemiss:
    """Sentinel value representing a cache miss.

    Returned by subclasses of :class:`CacheStore`.

    """




T = typing.TypeVar("T")


class CacheStore(abc.ABC, typing.Generic[T]):
    """Abstract Base Class. Container for cached items.

    :func:`cache` expects two abstract methods,
    :meth:`get <ponty.memo.CacheStore.get>` and
    :meth:`set <ponty.memo.CacheStore.set>`, and
    :func:`invalidate` expects one,
    :meth:`remove <ponty.memo.CacheStore.remove>`.
    All three must return awaitables.

    Generic on one variable, the type T of the cached item.

    """

    @abc.abstractmethod
    async def get(self, key: str) -> typing.Union[T, type[cachemiss]]:
        """Fetch the cached value.

        Errors are not captured.

        :param key: unique id for the cached item
        :returns: the cached item,
          or the :class:`cachemiss` sentinel if it does not exist
        :rtype: Union[T, type[:class:`cachemiss`]]

        """

    @abc.abstractmethod
    async def set(self, key: str, data: T) -> None:
        """Add an item to the cache.

        :param key: unique id for the item
        :param data: the item to be cached

        """

    @abc.abstractmethod
    async def remove(self, key: str) -> bool:
        """Remove an item from the cache.

        :param key: unique id for the cached item
        :returns: True if the item is found and removed, False otherwise

        """




_registry = Registry[tuple[CacheStore, Lock]]()


def cache(store: CacheStore, antistampede: Lock, name: str = ""):
    """Cache the decorated function's return value. Not thread-safe.

    As a rule of thumb, storage mechanics for a cache are
    implemented in `store`, and synchronization rules are handled
    by `antistampede`.
    See the :func:`localcache`
    `source ↗ <https://github.com/csira/ponty/blob/main/ponty/memo/cache/local.py>`__
    for an example.

    :param store: container, implementing get/set mechanics for cached items
    :param antistampede: instance of :class:`ponty.memo.Lock`;
      blocks on simultaneous access to the requested key to avoid a stampede
    :param name: if provided, registers the cache for use by
      :func:`invalidate`. Must be unique

    """
    def wraps(f):
        if name:
            _registry.add(name, (store, antistampede))

        @functools.wraps(f)
        async def wrapper(*a, **kw):
            key = _hash_args(*a, **kw)

            async with antistampede.lock(key):
                data = await store.get(key)
                if data is not cachemiss:
                    return data

                data = await f(*a, **kw)
                await store.set(key, data)

            return data

        return wrapper
    return wraps


@asynccontextmanager
async def invalidate(cachename: str, *a, **kw) -> typing.AsyncIterator[None]:
    """Context manager. Invalidates an item in the cache.

    Waits for then holds the cache's lock until the context manager exits.
    This prevents simultaneous fetches from re-cache-ing the item before
    mutations are committed. This also means functions calling 'invalidate'
    CANNOT be wrapped with a cache decorator, as the decorator will already
    hold the lock.

    :param cachename: name of the registered cache.
      Must match :func:`cache`'s `name` parameter

    Note the \*arg/\**kwarg combo must match the arguments to the
    cache-decorated function EXACTLY in order to get a key hit. E.g.,

    .. code-block:: python
        :emphasize-lines: 2,7,9

        @localcache(name="foo")
        async def get_foo(foo_id):
            ...


        async def update_foo(foo_id, ...):
            async with invalidate("foo", foo_id):  # this hits
                ...
            async with invalidate("foo", foo_id=foo_id):  # this does not
                ...

    """
    key = _hash_args(*a, **kw)

    try:
        store, antistampede = _registry.get(cachename)
    except KeyError:
        warnings.warn(f"'{cachename}' is not registered", category=RuntimeWarning)
        yield
    else:
        async with antistampede.lock(key):
            await store.remove(key)
            yield


def _hash_args(*a, **kw) -> str:
    args = a + tuple(sorted(kw.items()))
    encoded = json.dumps(args).encode("utf-8")
    return hashlib.sha1(encoded).hexdigest()
