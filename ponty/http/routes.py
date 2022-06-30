import typing

import aiohttp.web


_route_table = aiohttp.web.RouteTableDef()


route = _route_table.route
get = _route_table.get
put = _route_table.put
post = _route_table.post
delete = _route_table.delete
patch = _route_table.patch


def route_iter() -> typing.Iterator[tuple[str, str]]:
    for route in _route_table:
        yield route.method, route.path


def mount_routes(
    app: aiohttp.web.Application,
    *route_tables: aiohttp.web.RouteTableDef,
) -> None:

    app.router.add_routes(_route_table)
    for rt in route_tables:
        app.router.add_routes(rt)
