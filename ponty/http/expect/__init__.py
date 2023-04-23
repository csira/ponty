import aiohttp.web

from ponty.errors import raise_status
from ponty.http.expect.body import (
    ParsedJsonBody,
    ValidatedJsonBody,
)
from ponty.http.expect.header import (
    ContentLength,
    ContentType,
    Header,
)
from ponty.http.expect.query import (
    PosIntQueryParameter,
    QueryParameter,
    StringQueryParameter,
)
from ponty.http.expect.req import (
    expect,
    JsonBody,
    Request,
    TextBody,
)
from ponty.http.expect.route import (
    PosIntRouteParameter,
    RouteParameter,
    StringRouteParameter,
)


class AIOHttpReq:
    """Forwards along the
    `aiohttp.web.Request <https://docs.aiohttp.org/en/latest/web_reference.html#aiohttp.web.Request>`__.

    """
    def __get__(self, obj: Request, objtype: type[Request]) -> aiohttp.web.Request:
        return obj.req


class Cookie:
    """Extracts request cookie `name`.

    :param str name: cookie name

    :param bool required:
      if True, throws a 400 if the cookie is not provided

    :param str default:
      default value, if the cookie is not present

    :param int errorcode:
      HTTP status code raised, if the cookie is required and not supplied

    """
    def __init__(
        self,
        *,
        name: str,
        required: bool = False,
        default: str = "",
        errorcode: int = 400,
    ):
        self._name = name
        self._required = required
        self._default = default
        self._errorcode = errorcode

    def __get__(self, obj: Request, objtype: type[Request]) -> str:
        try:
            return obj.req.cookies[self._name]
        except KeyError:
            if self._required:
                raise_status(self._errorcode)
            return self._default
