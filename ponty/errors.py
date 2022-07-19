import functools
import json
import typing
from typing import Awaitable, Callable, TypeVar
from typing_extensions import ParamSpec

import aiohttp.web


class PontyError(Exception):

    status_code = 500

    def __init__(
        self,
        *,
        text: str = None,
        body: typing.Any = None,
        **kw
    ):
        if text is not None and body is not None:
            raise ValueError

        super().__init__()
        self.text = text
        self.body = body
        self.kw = kw


class DoesNotExist(PontyError):

    status_code = 404


class ValidationError(PontyError):

    status_code = 400


class Locked(PontyError):

    status_code = 409




P = ParamSpec("P")
R = TypeVar("R")


def error_trap(f: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    @functools.wraps(f)
    async def wrapper(*a: P.args, **kw: P.kwargs) -> R:
        try:
            return await f(*a, **kw)
        except PontyError as e:
            raise_status(
                e.status_code,
                text=e.text,
                body=e.body,
                **e.kw
            )
    return wrapper


def raise_status(
    status: int,
    *,
    text: str = None,
    body: typing.Any = None,
    content_type: str = None,
    **kw
) -> typing.NoReturn:

    if text is not None and body is not None:
        raise ValueError

    if body:
        text = json.dumps(body)
        content_type = "application/json"

    class MyExc(aiohttp.web.HTTPException):
        status_code = status

    raise MyExc(text=text, content_type=content_type, **kw)
