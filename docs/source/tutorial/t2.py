import logging

from ponty import (
    get,
    expect,
    render_json,
    Request,
    startmeup,
    StringRouteParameter,
)


class HelloReq(Request):

    name = StringRouteParameter()


@get(f"/hello/{HelloReq.name}")
@expect(HelloReq)
@render_json
async def handler(name: str):
    return {"greeting": f"hi {name}!"}


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    startmeup(port=8000)
