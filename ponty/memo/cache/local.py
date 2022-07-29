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

    ttl_ms: millis to expiry. Use 0 (the default) for no expiry
    maxwait_ms: millis to wait for a lock to resolve.
                Throws "Stampede" error when (n * pulse) > maxwait
    pulse_ms: antistampede recheck frequency
    maxsize: evict least recently used values once the cache reaches <maxsize> elements
    name: providing a name registers the cache, so it can be used by 'invalidate'

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
