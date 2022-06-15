from dataclasses import asdict
import functools

import aiohttp.web
import jsonschema

from ponty.errors import error_trap
from ponty.http.schema import validator_for_dataclass
from ponty.utils import now_millis


def render(f):
    @functools.wraps(f)
    @error_trap
    async def wrapper(*a, **kw) -> aiohttp.web.Response:
        return aiohttp.web.json_response({
            "now": (start := now_millis()),
            "data": await f(*a, **kw),
            "elapsed": now_millis() - start,
        })
    return wrapper


def render_dc(cls):
    validator = validator_for_dataclass(cls)

    def wraps(f):
        @functools.wraps(f)
        @render
        async def wrapper(*a, **kw):
            inst = await f(*a, **kw)
            body = asdict(inst)

            try:
                validator.validate(body)
            except jsonschema.ValidationError as e:
                raise aiohttp.web.HTTPInternalServerError(text=e.message)

            return body
        return wrapper

    return wraps
