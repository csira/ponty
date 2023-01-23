from typing import AsyncIterator, Callable, Sequence
from typing_extensions import TypeAlias

import aiohttp.web

from ponty.http.routes import mount_routes, route_iter


Provider: TypeAlias = Callable[[aiohttp.web.Application], AsyncIterator[None]]


def startmeup(
    *,
    port: int,
    providers: Sequence[Provider] = (),
    route_tables: Sequence[aiohttp.web.RouteTableDef] = (),
) -> None:
    """The main entrypoint for your application. Kicks off the server event loop.

    :param port: TCP/IP port for HTTP server. No default, must be provided
    :param Sequence[Provider] providers: see :ref:`Providers`
    :param route_tables: Optional sequence of
      `aiohttp.web.RouteTableDef <https://docs.aiohttp.org/en/stable/web_reference.html#routetabledef>`_
      instances

    """
    app = aiohttp.web.Application()

    for p in providers:
        app.cleanup_ctx.append(p)

    mount_routes(app, *route_tables)
    _echo_routes()

    aiohttp.web.run_app(app, port=port)


def _echo_routes():
    print()
    print("serving:")
    for method, path in route_iter():
        print(method, "\t", path)
    print()
