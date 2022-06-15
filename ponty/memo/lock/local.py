from ponty.memo.lock.base import SentinelStore, Lock


class _Sentinels(SentinelStore):

    def __init__(self):
        super().__init__()
        self._sentinels: set[str] = set()

    async def exists(self, key: str) -> bool:
        return key in self._sentinels

    async def add(self, key: str) -> None:
        self._sentinels.add(key)

    async def remove(self, key: str) -> None:
        self._sentinels.remove(key)


def locallock(**kw) -> Lock:
    """Mutex. Coordinates across coroutines. Not thread-safe."""
    return Lock(sentinels=_Sentinels(), **kw)
