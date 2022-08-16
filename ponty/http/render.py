import functools

import aiohttp.web

from ponty.utils import now_millis


def render_json(f):
    """
    Package the decorated function's return via
    `aiohttp.web.json_response <https://docs.aiohttp.org/en/stable/web_reference.html#json-response>`_,
    with a body in the form:

    .. code-block:: python

        {
            "now": <current epoch timestamp, in millis>,
            "data": <function return>,
            "elapsed": <time elapsed, in millis>,
        }

    """
    @functools.wraps(f)
    async def wrapper(*a, **kw) -> aiohttp.web.Response:
        return aiohttp.web.json_response({
            "now": (start := now_millis()),
            "data": await f(*a, **kw),
            "elapsed": now_millis() - start,
        })
    return wrapper
