import json
import typing

import aiohttp.web
import jsonschema  # type: ignore

from ponty.http.schema import (
    dataclass_to_jsonschema,
    validator_for_schema,
    validator_from_file,
)
from ponty.http.expect.req import JsonBody, Request
from ponty.types_ import DataclassProtocol
from ponty.utils import logical_xor


class ValidatedJsonBody(JsonBody):

    def __init__(
        self,
        *,
        filepath: str = None,
        schema: dict[str, typing.Any] = None,
    ):
        super().__init__()

        if not logical_xor(filepath, schema):
            raise RuntimeError("only one of filepath, schema may be specified")

        if filepath:
            self._validator = validator_from_file(filepath)
        else:
            self._validator = validator_for_schema(schema)

    def __get__(self, obj: Request, objtype: type[Request]):
        body = super().__get__(obj, objtype)

        try:
            self._validator.validate(body)
        except jsonschema.ValidationError as e:
            raise aiohttp.web.HTTPBadRequest(text=e.message)

        return body


D = typing.TypeVar("D", bound=DataclassProtocol)


class ParsedJsonBody(ValidatedJsonBody, typing.Generic[D]):

    def __init__(self, cls: type[D], filepath: str = None):
        self._cls = cls

        if filepath:
            super().__init__(filepath=filepath)
        else:
            super().__init__(schema=dataclass_to_jsonschema(cls))

    def __get__(self, obj: Request, objtype: type[Request]) -> D:
        body = super().__get__(obj, objtype)
        return self._cls(**body)
