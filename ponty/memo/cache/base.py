import abc
from contextlib import asynccontextmanager
import functools
import hashlib
import json
import typing

from ponty.memo.lock.base import Lock, Locked
from ponty.registry import Registry


class Stampede(Locked): ...


class cachemiss: ...




T = typing.TypeVar("T")


class CacheStore(abc.ABC, typing.Generic[T]):

    @abc.abstractmethod
    async def get(self, key: str) -> typing.Union[T, type[cachemiss]]:
        """Return the cached value or the `cachemiss` sentinel. Errors are not captured."""

    @abc.abstractmethod
    async def set(self, key: str, data: T) -> None: ...

    @abc.abstractmethod
    async def remove(self, key: str) -> bool: ...




_registry = Registry[tuple[CacheStore, Lock]]()


def cache(store: CacheStore, antistampede: Lock, name: str = ""):
    """Cache the decorated function's return value. Not thread-safe.

    store: container (or proxy), implementing get/set mechanics for cached items
    antistampede: guard class, blocks on simultaneous access to the requested
                  key to avoid a stampede
    name: providing a name registers the cache, so it can be used by 'invalidate' below

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
async def invalidate(name: str, *a, **kw) -> typing.AsyncIterator[None]:
    """Invalidate an item in cache <name>.

    Also waits for and holds the cache's lock until the context manager exits.
    This is to prevent simultaneous fetches from re-cache-ing the item before
    mutations are committed.

    Note the *arg/**kwarg combo must match the arguments to the cache-decorated
    function EXACTLY in order to get a key hit. E.g.

    @localcache(name="foo", ttl_ms=60000)
    async def get_foo(foo_id):
        ...

    async def update_foo(foo_id, ...):
        async with invalidate("foo", foo_id):  # this works
            ...
        async with invalidate("foo", foo_id=foo_id):  # this does not
            ...

    """
    store, antistampede = _registry.get(name)
    key = _hash_args(*a, **kw)

    async with antistampede.lock(key):
        await store.remove(key)
        yield


def _hash_args(*a, **kw) -> str:
    args = a + tuple(sorted(kw.items()))
    encoded = json.dumps(args).encode("utf-8")
    return hashlib.sha1(encoded).hexdigest()
