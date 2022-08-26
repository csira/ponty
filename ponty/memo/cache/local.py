from collections import deque
import typing
import warnings

from ponty.memo.cache.base import CacheStore, cache, cachemiss, Stampede
from ponty.memo.lock.local import locallock
from ponty.utils import now_millis


T = typing.TypeVar("T")


class _LRUStore(CacheStore[T]):

    def __init__(self, ttl_ms: int, maxsize: int):
        super().__init__()

        if ttl_ms < 0:
            raise ValueError("negative ttl is nonsense")
        self._ttl_ms: typing.Final[int] = ttl_ms

        if maxsize < 0:
            raise ValueError("negative maxsize is nonsense")
        if maxsize == 0:
            warnings.warn("Cache without maxsize may grow endlessly, beware.")
        self._maxsize: typing.Final[int] = maxsize

        self._cache: dict[str, tuple[typing.Union[int, None], T]] = dict()
        self._lru: deque[str] = deque()

    async def get(self, key: str) -> typing.Union[T, type[cachemiss]]:
        try:
            expiry, data = self._cache[key]
        except KeyError:
            return cachemiss

        if expiry is not None and expiry < now_millis():
            await self.remove(key)
            return cachemiss

        # rotate key to the end of the LRU queue
        self._lru.remove(key)
        self._lru.append(key)

        return data

    async def set(self, key: str, data: T) -> None:
        if self._ttl_ms == 0:
            expiry = None
        else:
            expiry = now_millis() + self._ttl_ms

        self._cache[key] = (expiry, data)
        self._lru.append(key)
        await self._sizecheck()

    async def remove(self, key: str) -> bool:
        try:
            self._cache.pop(key)
        except KeyError:
            return False
        else:
            self._lru.remove(key)
        return True

    async def _sizecheck(self) -> None:
        if not self._maxsize:
            return

        while len(self._lru) > self._maxsize:
            key = self._lru.popleft()
            self._cache.pop(key)


def localcache(
    *,
    ttl_ms: int = 0,
    maxwait_ms: int = 1000,
    pulse_ms: int = 50,
    maxsize: int = 128,
    name: str = "",
):
    """Process-RAM LRU memoizer with antistampede.

    Good for small frequently-used datasets (high ttl) or volatile
    stampede-likely objects (low ttl).

    :param ttl_ms: millis to expiry. Use 0 (the default) for no expiry
    :param maxwait_ms: millis to wait for a lock to resolve.
      Throws :class:`Stampede` error when :math:`(n * pulse\_ms) > maxwait\_ms`
    :param pulse_ms: antistampede recheck frequency
    :param maxsize: evict least recently used values once the cache reaches
      `maxsize` elements
    :param name: Optional. Providing a name registers the cache, so it can be
      used by :func:`invalidate`


    Here is an example that demonstrates stampede control.
    With `maxwait_ms = 0`, this operates as a mandatory lock:

    .. code-block:: python
        :emphasize-lines: 13

        import asyncio

        from ponty import get, render_json
        from ponty.memo import localcache


        @get("/cachetest")
        @render_json
        async def _locktest(_):
            return await _fetch()


        @localcache(maxwait_ms=0)
        async def _fetch():
            await asyncio.sleep(1)  # some expensive operation
            return {"key": "value"}


    For five simultaneous requests,
    the first acquires the lock and begins work
    while the others are immediately declined:

    .. code-block:: bash

        $ for i in {1..5}; do curl localhost:8080/cachetest -v & done

        < HTTP/1.1 409 Conflict
        < Date: Tue, 23 Aug 2022 21:49:12 GMT

        < HTTP/1.1 409 Conflict
        < Date: Tue, 23 Aug 2022 21:49:12 GMT

        < HTTP/1.1 409 Conflict
        < Date: Tue, 23 Aug 2022 21:49:12 GMT

        < HTTP/1.1 409 Conflict
        < Date: Tue, 23 Aug 2022 21:49:12 GMT

        < HTTP/1.1 200 OK
        < Date: Tue, 23 Aug 2022 21:49:13 GMT
        {"now": 1661291352844, "data": {"key": "value"}, "elapsed": 1006}


    Now that the item is cached,
    running this again gives five immediate cache hits:

    .. code-block:: bash

        $ for i in {1..5}; do curl localhost:8080/cachetest & done
        {"now": 1661291746863, "data": {"key": "value"}, "elapsed": 0}
        {"now": 1661291746863, "data": {"key": "value"}, "elapsed": 0}
        {"now": 1661291746863, "data": {"key": "value"}, "elapsed": 0}
        {"now": 1661291746863, "data": {"key": "value"}, "elapsed": 0}
        {"now": 1661291746863, "data": {"key": "value"}, "elapsed": 0}


    Bump to `maxwait_ms = 2000` and clear the cache:

    .. code-block:: bash

        $ for i in {1..5}; do curl localhost:8080/cachetest & done
        {"now": 1661396864744, "data": {"key": "value"}, "elapsed": 1003}
        {"now": 1661396864744, "data": {"key": "value"}, "elapsed": 1043}
        {"now": 1661396864744, "data": {"key": "value"}, "elapsed": 1044}
        {"now": 1661396864744, "data": {"key": "value"}, "elapsed": 1045}
        {"now": 1661396864744, "data": {"key": "value"}, "elapsed": 1045}

    The first request is the only one doing work here;
    the others wait up to two seconds,
    checking in every `pulse_ms = 50` milliseconds (the default)
    to see if a result is available.

    """
    antistampede = locallock(
        maxwait_ms=maxwait_ms,
        pulse_ms=pulse_ms,
        timeout_error=Stampede,
    )

    return cache(
        store=_LRUStore(ttl_ms, maxsize),
        antistampede=antistampede,
        name=name,
    )
