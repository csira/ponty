import aiohttp.web


class Header:

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

    def __init__(self, **kw):
        super().__init__(key="content-length", **kw)


class ContentType(Header):

    def __init__(self, **kw):
        super().__init__(key="content-type", **kw)
