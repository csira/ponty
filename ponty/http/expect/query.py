import typing

import aiohttp.web


class QueryParameter:
    """Extracts the value of query parameter with name `key` from the URI.

    :param str key: if provided, query parameter key name.
      By default, uses descriptor `__set_name__` to fetch the variable name

    :param bool required:
      if True, throws a 400 if the query parameter is not provided

    :param str default:
      default value, if the query param is not provided


    .. code-block:: python
        :emphasize-lines: 12

        from ponty import (
            expect,
            get,
            render_json,
            QueryParameter,
            Request,
        )


        class HelloReq(Request):

            punc = QueryParameter(default="!")


        @get("/hello")
        @expect(HelloReq)
        @render_json
        async def greet(punc: str):
            return {"greeting": f"hello world{punc}"}


    .. code-block:: bash
        :caption: the default in action
        :emphasize-lines: 4

        $ curl localhost:8080/hello | python -m json.tool
        {
            "data": {
                "greeting": "hello world!"
            },
            "elapsed": 0,
            "now": 1660439305592
        }


    .. code-block:: bash
        :caption: overriding the default
        :emphasize-lines: 4

        $ curl localhost:8080/hello?punc=. | python -m json.tool
        {
            "data": {
                "greeting": "hello world."
            },
            "elapsed": 0,
            "now": 1660439305592
        }

    """
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
    """
    Inherits :class:`QueryParameter`.
    In addition to :class:`QueryParameter` behavior,
    validates the query parameter against a set of legal values.
    Throws a 400 in the event of a mismatch.

    :param values: legal values for the query parameter
    :param kw: additional parameters forwarded to :class:`QueryParameter`


    .. code-block:: python
        :emphasize-lines: 22

        from ponty import (
            expect,
            get,
            render_json,
            QueryParameterEnum,
            Request,
            StringRouteParameter,
        )


        _hellos: dict[str, str] = {
            "en": "hello",
            "es": "hola",
            "no": "hallo",
        }


        class HelloReq(Request):

            name = StringRouteParameter()
            lang = QueryParameterEnum(
                values=_hellos.keys(),
                default="en",
            )


        @get(f"/hello/{HelloReq.name}")
        @expect(HelloReq)
        @render_json
        async def ahoy(name: str, lang: str):
            # no need to trap the KeyError here, the descriptor has already
            # validated `lang` is a key in `_hellos`
            hi = _hellos[lang]
            return {"greeting": f"{hi} {name}!"}


    .. code-block:: bash

        $ curl "localhost:8080/hello/muchacho?lang=es" | python -m json.tool
        {
            "data": {
                "greeting": "hola muchacho!"
            },
            "elapsed": 0,
            "now": 1660440618107
        }

    """
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
