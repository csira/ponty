import typing


T = typing.TypeVar("T")


class Registry(typing.Generic[T]):

    def __init__(self):
        self._registry: dict[str, T] = {}

    def __contains__(self, name: str) -> bool:
        return name in self._registry

    def add(self, name: str, obj: T) -> None:
        if name in self:
            raise RuntimeError(f"'{name}' already registered")
        self._registry[name] = obj

    def get(self, name: str) -> T:
        return self._registry[name]
