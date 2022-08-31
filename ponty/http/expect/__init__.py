import functools
import inspect

import aiohttp.web

from ponty.http.expect.body import (
    ValidatedJsonBody,
    ParsedJsonBody,
)
from ponty.http.expect.header import (
    Header,
    ContentLength,
    ContentType,
)
from ponty.http.expect.query import QueryParameter, QueryParameterEnum
from ponty.http.expect.req import (
    expect,
    Request,
    JsonBody,
    TextBody,
)
from ponty.http.expect.route import (
    RouteParameter,
    PosIntRouteParameter,
    StringRouteParameter,
)


class AIOHttpReq:
    """Forwards along the
    `aiohttp.web.Request <https://docs.aiohttp.org/en/latest/web_reference.html#aiohttp.web.Request>`__.

    """
    def __get__(self, obj: Request, objtype: type[Request] = None) -> aiohttp.web.Request:
        return obj.req


class Cookie:
    """Extracts request cookie `name`.

    :param str name: cookie name

    """
    def __init__(self, *, name: str):
        self._name = name

    def __get__(self, obj: Request, objtype: type[Request] = None) -> str:
        return obj.req.cookies[self._name]
