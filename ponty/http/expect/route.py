import typing

from ponty.http.expect.req import Request


T = typing.TypeVar("T")


class RouteParameter(typing.Generic[T]):
    """
    The *RouteParameter* descriptor is used to identify and extract
    variable resources from the URI. It is generic on one variable.

    When invoked from an instance, returns the variable part of the resolved route.

    When invoked from a class, returns the `{identifier:regex}` rendering
    required for path matching.
    (See `Variable Resources <https://docs.aiohttp.org/en/stable/web_quickstart.html#variable-resources>`_.)
    Particularly useful in an f-string (example below).

    :param str pattern: custom regular expression to match the variable part
    :param cast_to: converts the variable part to type `T`


    New reusable "matchers" can be created like so:

    .. code-block:: python
       :emphasize-lines: 9,17,22

        from ponty import (
            expect,
            get,
            Request,
            RouteParameter,
        )


        class FiveLetters(RouteParameter[str]):

            def __init__(self):
                super().__init__(pattern="[a-zA-Z]{5}")


        class MyReq(Request):

            id = FiveLetters()


        @get(f"/obj/{MyReq.id}")
        @expect(MyReq)
        async def handler(id: str):
            ...

    """
    def __init__(
        self,
        *,
        pattern: str,
        cast_to: typing.Callable[[str], T] = None,
    ):
        self._pattern = pattern
        self._cast_func = cast_to

    def __set_name__(self, owner: type[Request], name: str):
        self._key = name

    @typing.overload
    def __get__(self, obj: None, objtype: type[Request]) -> str: ...

    @typing.overload
    def __get__(self, obj: Request, objtype: type[Request]) -> T: ...

    def __get__(
        self,
        obj: typing.Optional[Request],
        objtype: type[Request] = None,
    ) -> typing.Union[T, str]:

        if obj is None:
            return f"{{{self._key}:{self._pattern}}}"

        val = obj.req.match_info[self._key]
        if self._cast_func:
            return self._cast_func(val)
        return val


class PosIntRouteParameter(RouteParameter[int]):
    """
    Inherits :class:`RouteParameter`.
    Matches on a sequence of digits, ``\d+``.

    """
    def __init__(self):
        super().__init__(pattern="\d+", cast_to=int)


class StringRouteParameter(RouteParameter[str]):
    """
    Inherits :class:`RouteParameter`.
    Matches on strings, ``\w+``.

    """
    def __init__(self):
        super().__init__(pattern="\w+")
