import aiohttp.web


class Header:
    """
    Extracts request header `key`.

    :param str key: header name

    :param bool required:
      if True, throws a 400 if the request header is not provided

    :param str default:
      default value, if the header does not appear on the request

    """
    def __init__(self, *, key: str, required: bool = False, default: str = ""):
        self._key = key
        self._required = required
        self._default = default

    def __get__(self, obj, objtype=None) -> str:
        try:
            return obj.req.headers[self._key]
        except KeyError:
            if self._required:
                raise aiohttp.web.HTTPBadRequest
            return self._default


class ContentLength(Header):
    """Inherits :class:`Header`. Extracts the "content-length" header."""

    def __init__(self, **kw):
        super().__init__(key="content-length", **kw)


class ContentType(Header):
    """Inherits :class:`Header`. Extracts the "content-type" header."""

    def __init__(self, **kw):
        super().__init__(key="content-type", **kw)
