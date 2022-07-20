import functools

import aiohttp.web

from ponty.utils import now_millis


def render_json(f):
    @functools.wraps(f)
    async def wrapper(*a, **kw) -> aiohttp.web.Response:
        return aiohttp.web.json_response({
            "now": (start := now_millis()),
            "data": await f(*a, **kw),
            "elapsed": now_millis() - start,
        })
    return wrapper
