__all__ = ["dataclass_to_jsonschema", "Annotation"]


import dataclasses
from dataclasses import MISSING
import datetime
import enum
import numbers
import typing

from ponty.types_ import DataclassProtocol


class Annotation(dict[str, typing.Any]): ...




D = typing.TypeVar("D", bound=DataclassProtocol)


def dataclass_to_jsonschema(cls: type[D]) -> dict[str, typing.Any]:
    """Generate the jsonschema for a dataclass. Supports backreferences.

    Optionally, fields can be enriched by passing jsonschema keywords to Annotation.

    Additionally, the dataclass can be enriched with keywords by embedding
    a JsonSchema class (using Annotation as well).

    E.g.,


    @dataclasses.dataclass
    class Model:

        name: str
        body_style: typing.Literal["coupe", "sedan", "hatchback", "convertible", "wagon", "suv"]
        year: typing.Annotated[int, Annotation(minimum=1900, maximum=2050)]
        msrp: typing.Annotated[int, Annotation(description="MSRP, dollars.")]
        cylinders: int = 4


    @dataclasses.dataclass
    class Make:

        name: typing.Annotated[str, Annotation(description="Brand name")]
        models: list[Model]

        class JsonSchema:
            annotation = Annotation(description="Brand name", examples=["Toyota", "Honda"])

    """
    if not dataclasses.is_dataclass(cls):
        raise ValueError("Dataclasses only.")

    defs: dict[str, typing.Any] = {}
    schema = _cache_dataclass(cls, cls, defs, True)

    if defs:
        schema["$defs"] = defs

    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        **schema,
    }




def _cache_dataclass(cls, primary, defs, firstpass=False):
    if cls is primary:
        if firstpass:
            return _render_dataclass(cls, primary, defs)
        return {"allOf": [{"$ref": "#"}]}

    name = cls.__name__
    if name not in defs:
        defs[name] = _render_dataclass(cls, primary, defs)

    return {"allOf": [{"$ref": f"#/$defs/{name}"}]}


def _render_dataclass(cls, primary, defs):
    properties = {}
    required = []

    for field in dataclasses.fields(cls):
        schema = _lookup(field.type, primary, defs)
        if field.default is not MISSING:
            schema["default"] = field.default

        properties[field.name] = schema

        if field.default is MISSING and field.default_factory is MISSING:
            required.append(field.name)

    schema = {
        "properties": properties,
        "title": cls.__name__,
        "type": "object",
        **getattr(getattr(cls, "JsonSchema", {}), "annotation", {})
    }

    if required:
        schema["required"] = required

    return schema


def _lookup(field_type, primary, defs, **kw):
    if dataclasses.is_dataclass(field_type):
        return _cache_dataclass(field_type, primary, defs)

    if field_type is typing.Any:
        return {}

    if field_type is None or field_type is type(None):
        return {"type": "null", **kw}

    unscripted_type = typing.get_origin(field_type)
    args = typing.get_args(field_type)

    if unscripted_type is typing.Annotated:
        for anno in args[1:]:
            if isinstance(anno, Annotation):
                break
        else:
            anno = {}

        return _lookup(args[0], primary, defs, **anno)

    if unscripted_type is typing.Literal:
        return {"enum": list(args), **kw}

    if unscripted_type is typing.Union:  # also catches Optional
        # TODO list would be nicer? this is prob more reliable
        return {
            "anyOf": [_lookup(arg, primary, defs) for arg in args],
            **kw
        }

    if field_type is bool:
        return {"type": "boolean", **kw}
    if field_type is int:
        return {"type": "integer", **kw}
    if field_type is str:
        return {"type": "string", **kw}

    if field_type is dict or unscripted_type is dict:
        schema = {"type": "object", **kw}
        if len(args) == 2:
            t1, t2 = args
            if t1 is not str:
                raise Exception
            schema["additionalProperties"] = _lookup(t2, primary, defs)
        return schema

    if field_type is list or unscripted_type is list:
        schema = {"type": "array", **kw}
        if len(args) == 1:
            schema["items"] = _lookup(args[0], primary, defs)
        return schema

    if field_type is set or unscripted_type is set:
        schema = {"type": "array", "uniqueItems": True, **kw}
        if args:
            schema["items"] = _lookup(args[0], primary, defs)
        return schema

    if field_type is tuple or unscripted_type is tuple:
        schema = {"type": "array", **kw}

        if args:
            if len(args) == 2 and (args[1] is ...):
                schema["items"] = _lookup(args[0], primary, defs)
            else:
                schema["prefixItems"] = [_lookup(arg, primary, defs) for arg in args]
                schema["minItems"] = schema["maxItems"] = len(args)

        return schema

    if issubclass(field_type, datetime.datetime):  # subclass of datetime.date, so must come first
        return {"type": "string", "format": "date-time", **kw}
    if issubclass(field_type, datetime.date):
        return {"type": "string", "format": "date", **kw}
    if issubclass(field_type, numbers.Number):
        return {"type": "number", **kw}

    if issubclass(field_type, enum.Enum):
        name = field_type.__name__
        if name not in defs:
            defs[name] = {
                "title": name,
                "enum": [i.value for i in field_type],
                **kw
            }
        return {"allOf": [{"$ref": f"#/$defs/{name}"}]}

    raise Exception(f"no support for {field_type}/{unscripted_type}")


if __name__ == "__main__":
    import json

    @dataclasses.dataclass
    class Bar:
        x: int
        y: int

    @dataclasses.dataclass
    class Foo:
        name: typing.Annotated[str, Annotation(minLength=22, pattern=".*")]
        age: int
        blah: list[int]
        blargh: dict[str, Bar]
        blam: tuple[Bar, ...]
        favorite_color: typing.Optional[str]
        union_test: typing.Union[str, int] = 7

        class JsonSchema:
            annotation = Annotation(description="go you!")

    schema = dataclass_to_jsonschema(Foo)
    print(json.dumps(schema, indent=2))
