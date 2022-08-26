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
    """Mutex; coordinates across coroutines. Not thread-safe.

    :param maxwait_ms: total milliseconds to wait, before raising
      an exception with the caller.
      Raises `timeout_error` when :math:`n * pulse\_ms > maxwait\_ms`.
      If the lock is already held, the default `0` will cause the
      `timeout_error` to be raised immediately on a simultaneous access attempt

    :param pulse_ms: milliseconds between subsequent attempts
      to acquire the lock

    :param timeout_error: exception class raised when `maxwait_ms` exceeded.
      If provided, must be a subclass of :class:`Locked <ponty.memo.Locked>`


    A simple example that sleeps whenever the lock is acquired,
    in order to run out the 5-second clock on other waiting requests:

    .. code-block:: python
        :emphasize-lines: 9,19

        import asyncio
        import random
        import time

        from ponty import get, render_json
        from ponty.memo import locallock, Locked


        mylock = locallock(maxwait_ms=5000)  # concurrent requests wait 5 seconds max


        @get("/locktest")
        @render_json
        async def _locktest(_):
            secs = random.randint(1, 6)
            success = True

            try:
                async with mylock.lock("ponty"):  # "ponty" is the id of the protected resource
                    await asyncio.sleep(secs)
            except Locked:
                success = False

            return {
                "success": success,
                "secs": secs,
            }


    The five requests below are issued in parallel, so attempt to grab the lock
    at approximately the same time. Note how the first three acquire it at
    :math:`t = 0`, :math:`t = 1`, and :math:`t = 4`, respectively -  all
    beneath the 5-second timeout - while the last two time out at roughly the
    5-second mark. (With a larger timeout, they would have captured the lock
    at approx :math:`t = 8` and :math:`t = 10`.)

    .. code-block:: bash

        $ for i in {1..5}; do curl localhost:8080/locktest & done
        {"now": 1661271438402, "data": {"success": true, "secs": 1}, "elapsed": 1006}
        {"now": 1661271438402, "data": {"success": true, "secs": 3}, "elapsed": 4049}
        {"now": 1661271438402, "data": {"success": true, "secs": 4}, "elapsed": 8087}
        {"now": 1661271438403, "data": {"success": false, "secs": 2}, "elapsed": 5232}
        {"now": 1661271438404, "data": {"success": false, "secs": 5}, "elapsed": 5232}


    """
    return Lock(sentinels=_Sentinels(), **kw)
