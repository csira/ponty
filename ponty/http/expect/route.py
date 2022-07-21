import typing

from ponty.http.expect.req import Request


T = typing.TypeVar("T")


class RouteParameter(typing.Generic[T]):

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

    def __init__(self):
        super().__init__(pattern="\d+", cast_to=int)


class StringRouteParameter(RouteParameter[str]):

    def __init__(self):
        super().__init__(pattern="\w+")
