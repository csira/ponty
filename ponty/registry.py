import typing

from ponty.errors import PontyError


T = typing.TypeVar("T")


class Registry(typing.Generic[T]):

    def __init__(self):
        self._registry: dict[str, T] = {}

    def __contains__(self, name: str) -> bool:
        return name in self._registry

    def add(self, name: str, obj: T) -> None:
        if name in self:
            raise AlreadyRegistered(name)

        self._registry[name] = obj

    def get(self, name: str) -> T:
        try:
            return self._registry[name]
        except KeyError:
            raise Unregistered(name)


class AlreadyRegistered(PontyError): ...
class Unregistered(PontyError): ...
