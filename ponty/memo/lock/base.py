import abc
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
import typing

from ponty.errors import Locked


class SentinelStore(abc.ABC):

    @abc.abstractmethod
    async def exists(self, key: str) -> bool: ...

    @abc.abstractmethod
    async def add(self, key: str) -> None: ...

    @abc.abstractmethod
    async def remove(self, key: str) -> None: ...


@dataclass(frozen=True)
class Lock:
    """Basic mechanic for locking / antistampede. Not thread-safe.

    Operates as a mandatory lock by default. Control blocking by specifying
    the <maxwait_ms> parameter.

    sentinels: locker, providing add/remove operations and existence checking
    maxwait_ms: patience, in millis. Raises <timeout_error> when n * pulse > maxwait
    pulse_ms: attempt to acquire the lock approx every <pulse> milliseconds
    timeout_error: exception class raised when <maxwait_ms> exceeded.
                   If provided, must be a subclass of Locked.

    """
    sentinels: SentinelStore
    maxwait_ms: int = 0
    pulse_ms: int = 100
    timeout_error: type[Locked] = Locked

    @asynccontextmanager
    async def lock(self, key: str) -> typing.AsyncIterator[None]:
        elapsed = 0
        is_locked = await self.sentinels.exists(key)

        while is_locked and elapsed < self.maxwait_ms:
            await asyncio.sleep(self.pulse_ms * 0.001)
            elapsed += self.pulse_ms
            is_locked = await self.sentinels.exists(key)

        if is_locked:
            raise self.timeout_error(text=key)

        try:
            await self.sentinels.add(key)
            yield
        finally:
            await self.sentinels.remove(key)
