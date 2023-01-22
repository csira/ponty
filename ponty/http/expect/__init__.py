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

    :param bool required:
      if True, throws a 400 if the cookie is not provided

    :param str default:
      default value, if the cookie is not present

    """
    def __init__(self, *, name: str, required: bool = False, default: str = ""):
        self._name = name
        self._required = required
        self._default = default

    def __get__(self, obj: Request, objtype: type[Request] = None) -> str:
        try:
            return obj.req.cookies[self._name]
        except KeyError:
            if self._required:
                raise aiohttp.web.HTTPBadRequest
            return self._default
