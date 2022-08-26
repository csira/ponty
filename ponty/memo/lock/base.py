import abc
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
import typing

from ponty.errors import PontyError


class Locked(PontyError):
    """Returns a 409. Inherits :class:`PontyError <ponty.PontyError>`."""

    status_code = 409


class SentinelStore(abc.ABC):
    """Container for asset id's currently protected by a :class:`Lock`.

    Abstact Base Class.
    :class:`Lock` expects the three abstract methods below -
    :meth:`exists <ponty.memo.SentinelStore.exists>`,
    :meth:`add <ponty.memo.SentinelStore.add>`,
    :meth:`remove <ponty.memo.SentinelStore.remove>` -
    to return awaitables, whether they perform IO or not.
    (NB no context switch occurs if the method does not perform a
    blocking operation.) This constraint may be relieved in a future version.

    """

    @abc.abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if an asset is *currently* locked.

        :param key: unique id for the asset
        :returns: True if the asset is locked, False otherwise

        """

    @abc.abstractmethod
    async def add(self, key: str) -> None:
        """Take the lock on the asset.

        :param key: unique id for the asset

        """

    @abc.abstractmethod
    async def remove(self, key: str) -> None:
        """Release the lock on the asset.

        :param key: unique id for the asset

        """


@dataclass(frozen=True)
class Lock:
    """Basic mechanic for locking / antistampede.

    Operates as a mandatory lock by default. Control blocking by specifying
    the `maxwait_ms` parameter.

    :param sentinels: set-like container, providing add/remove operations and
      existence checking. Must be an instance of :class:`SentinelStore`

    :param maxwait_ms: total milliseconds to wait, before raising
      an exception with the caller.
      Raises `timeout_error` when :math:`n * pulse\_ms > maxwait\_ms`

    :param pulse_ms: milliseconds between subsequent attempts
      to acquire the lock

    :param timeout_error: exception class raised when `maxwait_ms` exceeded.
      If provided, must be a subclass of :class:`Locked`
    :type timeout_error: type[Locked]

    """
    sentinels: SentinelStore
    maxwait_ms: int = 0
    pulse_ms: int = 100
    timeout_error: type[Locked] = Locked

    @asynccontextmanager
    async def lock(self, key: str) -> typing.AsyncIterator[None]:
        """
        Context manager. Holds the lock on `key` until the block exits, or
        waits to acquire it until `maxwait_ms` milliseconds have elapsed.

        :param key: unique identifier for the asset whose access requires
          synchronization

        """
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
