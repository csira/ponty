import typing

import aiohttp.web


class QueryParameter:

    def __init__(
        self,
        *,
        key: str = None,
        required: bool = False,
        default: str = "",
    ):
        self._key = key
        self._required = required
        self._default = default

    def __set_name__(self, obj, name):
        if not self._key:
            self._key = name

    def __get__(self, obj, objtype=None) -> str:
        try:
            return obj.req.query[self._key]
        except KeyError:
            if self._required:
                raise aiohttp.web.HTTPBadRequest
            return self._default


class QueryParameterEnum(QueryParameter):

    def __init__(self, *, values: typing.Iterable[str], **kw):
        super().__init__(**kw)
        self._values = values

        if self._default and self._default not in values:
            raise ValueError(f"default '{self._default}' does not validate")

    def __get__(self, obj, objtype=None) -> str:
        val = super().__get__(obj, objtype)
        if val not in self._values:
            msg = f"{self._key} must be one of {{{','.join(self._values)}}}"
            raise aiohttp.web.HTTPBadRequest(text=msg)
        return val
