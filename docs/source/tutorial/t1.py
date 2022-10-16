import logging

from ponty import get, render_json, startmeup


@get("/hello")
@render_json
async def handler(_):
    return {"greeting": "hello world"}


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    startmeup(port=8000)
