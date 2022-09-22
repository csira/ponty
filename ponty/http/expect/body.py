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
    """
    Validates the deserialized request body against the given jsonschema.
    Invalid input immediately triggers a 400 response.

    Inherits :class:`JsonBody`.

    :param filepath: jsonschema file location
      (absolute, relative to PYTHONPATH, or relative to working directory).


    .. code-block:: json
        :caption: validator.json

        {
          "$schema": "http://json-schema.org/draft-07/schema#",
          "type": "object",
          "properties": {
            "first_name": { "type": "string" },
            "last_name": { "type": "string" }
          },
          "required": ["first_name", "last_name"]
        }


    .. code-block:: python

        from ponty import (
            expect,
            post,
            render_json,
            Request,
            ValidatedJsonBody,
        )


        class MyReq(Request):

            body = ValidatedJsonBody(filepath="validator.json")


        @post("/test")
        @expect(MyReq)
        @render_json
        async def handler(body):
            return {"name": f"{body['last_name']}, {body['first_name']}"}


    .. code-block:: bash
        :caption: success

        $ curl localhost:8080/test \\
            -H "content-type:application/json" \\
            -d '{"first_name": "Donald", "last_name": "Duck"}' | python -m json.tool
        {
            "data": {
                "name": "Duck, Donald",
            },
            "elapsed": 0,
            "now": 1660505985510
        }


    .. code-block:: bash
        :caption: error, "last_name" omitted
        :emphasize-lines: 6,9

        $ curl localhost:8080/test \\
            -H "content-type:application/json" \\
            -d '{"first_name": "Donald"}' \\
            -v
        ...
        < HTTP/1.1 400 Bad Request
        < Content-Type: text/plain; charset=utf-8
        ...
        'last_name' is a required property

    """
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
    """Holds the validated request body, structured as an instance of `cls`.

    Inherits :class:`ValidatedJsonBody`.

    :param dataclass cls: dataclass, into which the request body is marshalled.
      A custom jsonschema validator is automatically created by
      :func:`ponty.dataclass_to_jsonschema`

    :param filepath: if provided, path to the jsonschema file
      (see :class:`ValidatedJsonBody`).
      Supplants the dataclass-built default


    .. code-block:: python

        from dataclasses import asdict, dataclass
        import typing

        from ponty import (
            expect,
            post,
            render_json,
            Annotation,
            ParsedJsonBody,
            Request,
        )


        @dataclass(frozen=True)
        class Person:

            first_name: str
            last_name: str
            favorite_color: typing.Optional[str]
            height: typing.Annotated[int, Annotation(description="cm")]

            class JsonSchema:
                annotation = Annotation(description="request shape for a person")


        class NewPersonReq(Request):

            person = ParsedJsonBody(Person)


        @post("/person")
        @expect(NewPersonReq, mimetype="application/json")
        @render_json
        async def handler(person: Person):
            return asdict(person)


    .. code-block:: json
        :caption: the generated jsonschema
        :emphasize-lines: 22,27

        {
          "$schema": "http://json-schema.org/draft-07/schema#",
          "properties": {
            "first_name": {
              "type": "string"
            },
            "last_name": {
              "type": "string"
            },
            "favorite_color": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ]
            },
            "height": {
              "type": "integer",
              "description": "cm"
            }
          },
          "title": "Person",
          "type": "object",
          "description": "request shape for a person",
          "required": [
            "first_name",
            "last_name",
            "favorite_color",
            "height"
          ]
        }

    (note the highlighted lines, controlled by :class:`Annotation`)


    .. code-block:: bash
        :caption: success, echo back the request body

        $ curl localhost:8080/person \\
            -H "content-type:application/json" \\
            -d '{"first_name": "Mickey", "last_name": "Mouse", "favorite_color": "blue", "height": 1000}' \\
            -v | python -m json.tool
        > POST /person HTTP/1.1
        > Host: localhost:8080
        > User-Agent: curl/7.64.1
        > Accept: */*
        > content-type:application/json
        > Content-Length: 83
        >
        < HTTP/1.1 200 OK
        < Content-Type: application/json; charset=utf-8
        < Content-Length: 129
        < Date: Sun, 14 Aug 2022 21:04:35 GMT
        < Server: Python/3.9 aiohttp/3.7.3
        <
        {
            "data": {
                "favorite_color": "blue",
                "first_name": "Mickey",
                "height": 1000,
                "last_name": "Mouse"
            },
            "elapsed": 0,
            "now": 1660511075634
        }


    .. code-block:: bash
        :caption: error, missing "height"
        :emphasize-lines: 6,9

        $ curl localhost:8080/person \\
            -H "content-type:application/json" \\
            -d '{"first_name": "Mickey", "last_name": "Mouse", "favorite_color": "blue"}' \\
            -v
        ...
        < HTTP/1.1 400 Bad Request
        < Content-Type: text/plain; charset=utf-8
        ...
        'height' is a required property


    .. code-block:: bash
        :caption: error, wrong type for "height"
        :emphasize-lines: 6,8

        $ curl localhost:8080/person \\
            -H "content-type:application/json" \\
            -d '{"first_name": "Mickey", "last_name": "Mouse", "favorite_color": "blue", "height": "abc"}' \\
            -v
        ...
        < HTTP/1.1 400 Bad Request
        ...
        'abc' is not of type 'integer'

    """
    def __init__(self, cls: type[D], *, filepath: str = None):
        self._cls = cls

        if filepath:
            super().__init__(filepath=filepath)
        else:
            super().__init__(schema=dataclass_to_jsonschema(cls))

    def __get__(self, obj: Request, objtype: type[Request]) -> D:
        body = super().__get__(obj, objtype)
        return self._cls(**body)
