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
    for route in ( typing.cast(aiohttp.web.RouteDef, r) for r in _route_table ):
        yield route.method, route.path


def mount_routes(
    app: aiohttp.web.Application,
    *route_tables: aiohttp.web.RouteTableDef,
) -> None:

    app.router.add_routes(_route_table)
    for rt in route_tables:
        app.router.add_routes(rt)
