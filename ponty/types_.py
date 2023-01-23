from dataclasses import dataclass
import sys
from typing import Any, Protocol


if sys.version_info >= (3, 10):
    @dataclass
    class DataclassProtocol(Protocol):
        ...

else:
    class DataclassProtocol(Protocol):
        __dataclass_fields__: dict[str, Any]
