import typing


class DataclassProtocol(typing.Protocol):

    __dataclass_fields__: dict[str, typing.Any]
