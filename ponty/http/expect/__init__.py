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

    def __get__(self, obj, objtype=None) -> aiohttp.web.Request:
        return obj.req


class Cookie:

    def __init__(self, *, name: str):
        self._name = name

    def __get__(self, obj, objtype=None) -> str:
        return obj.req.cookies[self._name]
