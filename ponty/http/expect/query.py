import aiohttp.web

from ponty.http.expect.default_mixin import DefaultMixin


class QueryParameter(DefaultMixin):

    def __init__(
        self,
        *,
        key: str = None,
        required: bool = False,
        default: str = "",
    ):
        self._key = key
        super().__init__(required=required, default=default)

    def __set_name__(self, obj, name):
        if not self._key:
            self._key = name

    def __get__(self, obj, objtype=None) -> str:
        try:
            return obj.req.query[self._key]
        except KeyError:
            return self.get_default()


class QueryParameterEnum(QueryParameter):

    def __init__(self, *, values: tuple[str, ...], **kw):
        super().__init__(**kw)
        self._values = values

        if self._default and self._default not in values:
            raise TypeError(f"default '{self._default}' does not validate")

    def __get__(self, obj, objtype=None) -> str:
        val = super().__get__(obj, objtype)
        if val not in self._values:
            msg = f"{self._key} must be one of {{{','.join(self._values)}}}"
            raise aiohttp.web.HTTPBadRequest(text=msg)
        return val
