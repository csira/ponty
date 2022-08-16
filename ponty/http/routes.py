import functools
import typing

from aiohttp.hdrs import (
    METH_DELETE,
    METH_GET,
    METH_PATCH,
    METH_POST,
    METH_PUT,
)
import aiohttp.web

from ponty.errors import error_trap


_route_table = aiohttp.web.RouteTableDef()


def route(method: str, path: str, **kw):
    """
    Bind a (method, path) pair to its handler, and register with the master route table.

    :class:`PontyError`'s are automatically trapped and handled here.

    :param method: HTTP method, e.g. GET
    :param path: Relative path to resource.
      May contain braces {} for dynamic components,
      or references to :class:`RouteParameter` instances in an f-string
    :param kw: Additional arguments discussed
      `here <https://docs.aiohttp.org/en/latest/web_reference.html#aiohttp.web.UrlDispatcher.add_get>`__

    """
    def wraps(f):
        @_route_table.route(method, path, **kw)
        @error_trap
        @functools.wraps(f)
        async def wrapper(*a, **kw):
            return await f(*a, **kw)
        return wrapper
    return wraps


delete = functools.partial(route, METH_DELETE)
get = functools.partial(route, METH_GET)
patch = functools.partial(route, METH_PATCH)
post = functools.partial(route, METH_POST)
put = functools.partial(route, METH_PUT)




def route_iter() -> typing.Iterator[tuple[str, str]]:
    """Iterator, over routes on the primary route table.

    :return: (method, path) pairs
    :rtype: Iterator[tuple[str, str]]

    """
    for route in ( typing.cast(aiohttp.web.RouteDef, r) for r in _route_table ):
        yield route.method, route.path


def mount_routes(
    app: aiohttp.web.Application,
    *route_tables: aiohttp.web.RouteTableDef,
) -> None:

    app.router.add_routes(_route_table)
    for rt in route_tables:
        app.router.add_routes(rt)
