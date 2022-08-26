import asyncio
import functools
import random
import time


def now_millis() -> int:
    return int(time.time() * 1000)


def logical_xor(m, n) -> bool:
    """Logical xor. True if exactly one of {m, n} is truth-y.

    Equivalent to
        (m and not n) or (not m and n)

    NB: xor on two bools is logical since, on integers, logical xor is identical
    to bitwise xor when the domain is limited to {0, 1}

    """
    return bool(m) ^ bool(n)




def retry(
    *excs: type[Exception],
    max_retries: int = 1,
    t1_ms: int = 100,
    t2_ms: int = 4000,
    backoff_factor: float = 1,
    anticollision: bool = False,
):
    """Retry the wrapped function if the specified exception(s) are raised.

    Supports sync & async functions.

    :param excs: Exception class(es) to trap
    :param max_retries: max number of retries to attempt
    :param t1_ms: initial interval between retries, in millis
    :param t2_ms: max interval between retries, in millis
    :param backoff_factor:
      rate reduction factor for exponential backoff :math:`t = b^c`, where

        | t is the delay factor between calls
        | b = `backoff_factor` is the base
        | c is the number of failures observed so far

      :math:`b > 1` will reduce the retry rate,
      :math:`b = 1` will give consistent retry intervals, and
      :math:`b < 1` will accelerate retries (unusual choice).
      Set to 2 for run-of-the-mill binary exponential backoff.
    :param anticollision: a deterministic algorithm may be unsuitable when
      errors are caused by collisions, because each client will sleep for the
      same amount of time, leading to subsequent collisions ad infinitum.
      Pass True to treat :math:`b^c` as an upper bound on the
      time delay; in this case we will sleep for :math:`k * t1\_ms`, where k is
      a random integer on :math:`[0, \\lfloor b^c  \\rfloor)`.


    .. code-block:: python

        import random
        import time

        from ponty import retry


        @retry(KeyError, ValueError, max_retries=10, backoff_factor=2)
        def getval():
            i = random.choice(range(5))
            print(f"i = {i}, now = {time.time()}")

            if i == 0:
                return 42
            if i % 2:
                raise KeyError
            raise ValueError


    .. code-block:: bash

        >>> print(getval())
        i = 3, now = 1660102025.223419
        i = 3, now = 1660102025.328576
        i = 4, now = 1660102025.533844
        i = 1, now = 1660102025.939289
        i = 1, now = 1660102026.744708
        i = 2, now = 1660102028.347733
        i = 0, now = 1660102031.549533
        42

    """
    def backoff(n_failures: int) -> float:
        k = backoff_factor ** n_failures
        if anticollision:
            k = random.choice(range(int(k)))
        return min(k * t1_ms, t2_ms) * 0.001

    def wraps(f):

        @functools.wraps(f)
        def sync_wrapper(*a, **kw):
            for n_failures in range(max_retries+1):
                try:
                    return f(*a, **kw)
                except excs as e:
                    if n_failures == max_retries:
                        raise e

                time.sleep(backoff(n_failures))

        @functools.wraps(f)
        async def async_wrapper(*a, **kw):
            for n_failures in range(max_retries+1):
                try:
                    return await f(*a, **kw)
                except excs as e:
                    if n_failures == max_retries:
                        raise e

                await asyncio.sleep(backoff(n_failures))

        if asyncio.iscoroutinefunction(f):
            return async_wrapper
        return sync_wrapper

    return wraps
