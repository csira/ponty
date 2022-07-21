__all__ = [
    "dataclass_to_jsonschema",
    "Annotation",
    "validator_for_dataclass",
    "validator_for_schema",
    "validator_from_file",
]


import functools
import json

from jsonschema.validators import validator_for  # type: ignore

from ponty.http.schema.build import dataclass_to_jsonschema, Annotation


def validator_for_schema(schema):
    validator = validator_for(schema)
    validator.check_schema(schema)
    return validator(schema)


@functools.cache
def validator_for_dataclass(cls):
    schema = dataclass_to_jsonschema(cls)
    return validator_for_schema(schema)


@functools.cache
def validator_from_file(filepath: str):
    with open(filepath) as f:
        schema = json.load(f)
    return validator_for_schema(schema)
