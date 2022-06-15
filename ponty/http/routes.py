import aiohttp.web


_route_table = aiohttp.web.RouteTableDef()


get = _route_table.get
post = _route_table.post
put = _route_table.put
delete = _route_table.delete
patch = _route_table.patch


def mount_routes(
    app: aiohttp.web.Application,
    *route_tables: aiohttp.web.RouteTableDef,
) -> None:

    app.router.add_routes(_route_table)
    for rt in route_tables:
        app.router.add_routes(rt)
