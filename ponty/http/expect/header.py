from ponty.http.expect.default_mixin import DefaultMixin


class Header(DefaultMixin):

    def __init__(self, *, key: str, required: bool = False, default: str = ""):
        self._key = key
        super().__init__(required=required, default=default)

    def __get__(self, obj, objtype=None) -> str:
        try:
            return obj.req.headers[self._key]
        except KeyError:
            return self.get_default()


class ContentLength(Header):

    def __init__(self, **kw):
        super().__init__(key="content-length", **kw)


class ContentType(Header):

    def __init__(self, **kw):
        super().__init__(key="content-type", **kw)
