import typing
from typing import Callable, Iterable, Literal, Union

from ponty.errors import ValidationError
from ponty.http.expect.req import Request


class _Missing: ...

_MISSING = _Missing()


_T = typing.TypeVar("_T")


class QueryParameter(typing.Generic[_T]):
    """
    Extracts the value of query parameter with name `key` from the URI,
    if it's provided. Generic on one variable.

    :param str key: if provided, query parameter key name.
      By default, uses descriptor `__set_name__` to fetch the variable name

    :param bool required:
      if True, the query parameter will be treated as a mandatory
      component of the request;
      an HTTP 400 will be raised in the event no value is supplied.
      Default `False`

    :param _T default:
      default value, returned if the query param is not provided.
      Set `required=True` instead if this should be treated as an error condition.
      One of `required` or `default` must be provided

    :param cast_func:
      function to convert the string value provided to type `T`.
      If the function raises a `ValueError` when it fails,
      the error will be trapped and reraised as an HTTP 400

    :param Iterable[str] values:
      if supplied, validates the captured query parameter against these
      legal values.
      Throws a 400 in the event of a mismatch

    It's easiest to use :class:`StringQueryParameter` or
    :class:`PosIntQueryParameter` for simple cases in practice.
    Use the :class:`QueryParameter` base class to create new custom parsers,
    in the same way as :class:`RouteParameter`:


    .. code-block:: python
        :emphasize-lines: 22,34,40

        from ponty import (
            expect,
            get,
            render_json,
            QueryParameter,
            Request,
        )


        _boolish_vals: dict[str, bool] = {
            "1": True,
            "0": False,
            "yes": True,
            "no": False,
            "true": True,
            "false": False,
            "t": True,
            "f": False,
        }


        class BoolQueryParam(QueryParameter[bool]):

            def __init__(self, **kw):
                super().__init__(
                    cast_func=_boolish_vals.__getitem__,
                    values=_boolish_vals.keys(),
                    **kw
                )


        class HelloReq(Request):

            capitalize = BoolQueryParam(default=False)


        @get("/hello")
        @expect(HelloReq)
        @render_json
        async def greet(capitalize: bool):
            greeting = "hello world"
            if capitalize:
                greeting = greeting.upper()
            return {"greeting": greeting}


    .. code-block:: bash
        :caption: the default
        :emphasize-lines: 4

        $ curl localhost:8080/hello | python -m json.tool
        {
            "data": {
                "greeting": "hello world"
            },
            "elapsed": 0,
            "now": 1679444906510
        }


    .. code-block:: bash
        :caption: providing a non-default option
        :emphasize-lines: 4

        $ curl 'localhost:8080/hello?capitalize=yes' | python -m json.tool
        {
            "data": {
                "greeting": "HELLO WORLD"
            },
            "elapsed": 0,
            "now": 1679444906739
        }


    .. code-block:: bash
        :caption: providing an illegal value
        :emphasize-lines: 2,7,13

        $ curl 'localhost:8080/hello?capitalize=blah' -v
        > GET /hello?capitalize=blah HTTP/1.1
        > Host: localhost:8080
        > User-Agent: curl/7.79.1
        > Accept: */*
        >
        < HTTP/1.1 400 Bad Request
        < Content-Type: text/plain; charset=utf-8
        < Content-Length: 46
        < Date: Wed, 22 Mar 2023 00:21:44 GMT
        < Server: Python/3.9 aiohttp/3.7.3
        <
        capitalize must be one of {1,0,yes,no,true,false,t,f}

    """
    @typing.overload
    def __init__(
        self,
        *,
        key: str = "",
        required: Literal[False] = False,
        default: _T,
        cast_func: Callable[[str], _T],
        values: Iterable[str] = (),
    ): ...

    @typing.overload
    def __init__(
        self,
        *,
        key: str = "",
        required: Literal[True] = True,
        cast_func: Callable[[str], _T],
        values: Iterable[str] = (),
    ): ...

    def __init__(
        self,
        *,
        key: str = "",
        required: bool = False,
        default: Union[_T, _Missing] = _MISSING,
        cast_func: Callable[[str], _T],
        values: Iterable[str] = (),
    ):

        self._key = key
        self._required = required
        self._default = default
        self._cast_func = cast_func
        self._values = values

    def __set_name__(self, obj: Request, name: str) -> None:
        if not self._key:
            self._key = name

    def __get__(self, obj: Request, objtype: type[Request]) -> _T:
        if obj is None:
            raise TypeError

        try:
            val = obj.req.query[self._key]
        except KeyError:
            if self._required:
                msg = f"required query param '{self._key}' is missing"
                raise ValidationError(text=msg)

            return typing.cast(_T, self._default)

        if self._values and val not in self._values:
            vals = (str(v) for v in self._values)
            msg = f"{self._key} must be one of {{{','.join(vals)}}}"
            raise ValidationError(text=msg)

        try:
            return self._cast_func(val)
        except ValueError:
            msg = f"{val} could not be cast"
            raise ValidationError(text=msg)

        return val


class StringQueryParameter(QueryParameter[str]):
    """
    Inherits :class:`QueryParameter`.
    Treats the captured query param as a string.

    .. code-block:: python
        :emphasize-lines: 12

        from ponty import (
            expect,
            get,
            render_json,
            Request,
            StringQueryParameter,
        )


        class HelloReq(Request):

            punc = StringQueryParameter(default="!")


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

        $ curl 'localhost:8080/hello?punc=.' | python -m json.tool
        {
            "data": {
                "greeting": "hello world."
            },
            "elapsed": 0,
            "now": 1660439305592
        }


    A similar example, using `values`:

    .. code-block:: python
        :emphasize-lines: 22

        from ponty import (
            expect,
            get,
            render_json,
            Request,
            StringQueryParameter,
            StringRouteParameter,
        )


        _hellos: dict[str, str] = {
            "en": "hello",
            "es": "hola",
            "no": "hallo",
        }


        class HelloReq(Request):

            name = StringRouteParameter()
            lang = StringQueryParameter(
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

        $ curl 'localhost:8080/hello/muchacho?lang=es' | python -m json.tool
        {
            "data": {
                "greeting": "hola muchacho!"
            },
            "elapsed": 0,
            "now": 1660440618107
        }

    """
    def __init__(self, **kw):
        super().__init__(cast_func=str, **kw)


class PosIntQueryParameter(QueryParameter[int]):
    """
    Inherits :class:`QueryParameter`.
    Casts the captured query param to an integer, and validates it is non-negative.

    """
    def __init__(self, **kw):
        super().__init__(cast_func=int, **kw)

    def __get__(self, obj: Request, objtype: type[Request]) -> int:
        val = super().__get__(obj, objtype)
        if val < 0:
            raise ValidationError(text=f"{val} less than 0")
        return val
