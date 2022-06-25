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

    excs: Exception class(es) to trap
    max_retries: retry up to <max_retries> times
    t1_ms: initial interval between retries, in millis
    t2_ms: max interval between retries, in millis
    backoff_factor: rate reduction factor for exponential backoff t = b^c, where
        t is the delay factor between calls
        b == <backoff_factor> is the base
        c is the number of failures observed so far
        b > 1 will reduce the retry rate, b == 1 will give consistent retry
        intervals, and b < 1 will accelerate retries (unusual choice).
        Set <backoff_factor> = 2 for run-of-the-mill binary exponential backoff.
    anticollision: a deterministic algorithm may be unsuitable when errors are
        caused by collisions because each client will sleep for the same
        amount of time, leading to subsequent collisions ad infinitum.
        Pass <anticollision>=True to treat b^c as an upper bound on the
        time delay; in this case we will sleep for k * <t1_ms>, where k is a
        random integer on [ 0, floor(b^c) ).

    Supports sync & async functions.

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
