import functools
import json
import typing
from typing import Awaitable, Callable, TypeVar
from typing_extensions import ParamSpec

import aiohttp.web


class PontyError(Exception):
    """
    PontyError's may be raised anywhere within your program to immediately
    respond with an HTTP status code. Unhandled errors are reraised as
    `aiohttp.web.HTTPException <https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.HTTPException>`__.

    :param text: response body, as text/plain
    :param body: json-serializable response body
    :param kw: see parameter description for
      `aiohttp.web.HTTPException <https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.HTTPException>`__

    """
    status_code: int = 500  #: HTTP status code for the response. See the official IANA registry `here <https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml>`__

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
    """Returns a 404. Inherits :class:`PontyError`."""

    status_code = 404


class ValidationError(PontyError):
    """Returns a 400. Inherits :class:`PontyError`."""

    status_code = 400




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
    """
    Raise an `aiohttp.web.HTTPException <https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.HTTPException>`_
    for the given status code.

    :param status: HTTP status code
    :param text: response body
    :param body: json-serializable response body.
      Automatically sets the content-type header to 'application/json'.
      Only one of `text` or `body` may be supplied.
    :param content_type: value for the response's content-type header
    :param kw: additional params for `aiohttp.web.HTTPException <https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.HTTPException>`_


    .. code-block:: python
        :emphasize-lines: 3

        @get("/fail")
        async def handler(_):
            raise_status(400, body={"a": 1})


    .. code-block:: bash
        :emphasize-lines: 7,13

        $ curl localhost:8080/fail -v
        > GET /fail HTTP/1.1
        > Host: localhost:8080
        > User-Agent: curl/7.64.1
        > Accept: */*
        >
        < HTTP/1.1 400 Bad Request
        < Content-Type: application/json; charset=utf-8
        < Content-Length: 8
        < Date: Wed, 10 Aug 2022 02:28:55 GMT
        < Server: Python/3.9 aiohttp/3.7.3
        <
        {"a": 1}

    """
    if text is not None and body is not None:
        raise ValueError

    if body:
        text = json.dumps(body)
        content_type = "application/json"

    class MyExc(aiohttp.web.HTTPException):
        status_code = status

    raise MyExc(text=text, content_type=content_type, **kw)
