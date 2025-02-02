from dataclasses import Field
from typing import Any, ClassVar, Protocol


class DataclassProtocol(Protocol):

    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]
