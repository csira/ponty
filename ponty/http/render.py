import functools

import aiohttp.web

from ponty.utils import now_millis


def render_json(f):
    """
    Encode the decorated function's return value with
    `json.dumps <https://docs.python.org/3/library/json.html#json.dumps>`__,
    and package it into an HTTP
    `response <https://docs.aiohttp.org/en/stable/web_reference.html#json-response>`__.
    The JSON has the form:

    .. code-block:: text

        {
            "data": <function return value>,
            "elapsed": <time elapsed, in millis>,
            "now": <current epoch timestamp, in millis>,
        }

    e.g.,

    .. code-block:: python
        :emphasize-lines: 7

        from ponty import get, render_json


        @get("/hello")
        @render_json
        async def handler(_):
            return {"greeting": "hello world!"}


    .. code-block:: bash
        :emphasize-lines: 4

        $ curl localhost:8080/hello | python -m json.tool
        {
            "data": {
                "greeting": "hello world!"
            },
            "elapsed": 1,
            "now": 1660440618107
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
