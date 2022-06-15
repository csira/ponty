import functools
import json
import typing
from typing import Awaitable, Callable, TypeVar
from typing_extensions import ParamSpec

import aiohttp


class PontyError(Exception):

    def __init__(self, msg=None, *a, **kw):
        self.msg = msg
        super().__init__(*a, **kw)


class DoesNotExist(PontyError): ...
class ValidationError(PontyError): ...
class Locked(PontyError): ...




P = ParamSpec("P")
R = TypeVar("R")


def error_trap(f: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    @functools.wraps(f)
    async def wrapper(*a: P.args, **kw: P.kwargs) -> R:
        try:
            return await f(*a, **kw)
        except DoesNotExist as e:
            raise aiohttp.web.HTTPNotFound(text=e.msg)
        except ValidationError as e:
            raise aiohttp.web.HTTPBadRequest(text=e.msg)
        except Locked as e:
            raise aiohttp.web.HTTPConflict(text=e.msg)
    return wrapper


def raise_for_status(
    status: int,
    *,
    text: str = None,
    body = None,
    content_type: str = None,
    **kw
) -> typing.NoReturn:

    if text is not None and body is not None:
        raise TypeError

    if body:
        text = json.dumps(body)
        content_type = "application/json"

    class MyExc(aiohttp.web.HTTPException):
        status_code = status

    raise MyExc(text=text, content_type=content_type, **kw)
