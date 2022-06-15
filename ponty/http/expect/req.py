import functools
import inspect
import typing

import aiohttp.web


class JsonBody:

    def __get__(self, obj: "Request", objtype: type["Request"]):
        return obj._json


class TextBody:

    def __get__(self, obj: "Request", objtype: type["Request"]):
        return obj._text




T = typing.TypeVar("T", covariant=True)


@typing.runtime_checkable
class _DataDescriptor(typing.Protocol[T]):
    def __get__(self, obj, objtype=None) -> T: ...




class _Base(type):

    def __new__(cls, name, bases, dct):
        the_class = super().__new__(cls, name, bases, dct)

        fieldnames = []
        for key, val in dct.items():
            if isinstance(val, _DataDescriptor):
                fieldnames.append(key)

            if isinstance(val, JsonBody):
                the_class._extract_json = True
            if isinstance(val, TextBody):
                the_class._extract_text = True

        the_class._fieldnames = tuple(fieldnames)
        return the_class


class Request(metaclass=_Base):

    _fieldnames: tuple[str, ...] = ()
    _extract_json: bool = False
    _extract_text: bool = False

    def __init__(self, req: aiohttp.web.Request):
        self.req = req
        self._json = None
        self._text: typing.Optional[str] = None

    @property
    def _fields(self) -> dict[str, typing.Any]:
        return {name: getattr(self, name) for name in self._fieldnames}

    async def _prepare(self) -> None:
        if self._extract_json:
            mimetype = self.req.headers["content-type"]
            if "application/json" not in mimetype:
                raise aiohttp.web.HTTPUnsupportedMediaType
            self._json = await self.req.json()

        if self._extract_text:
            self._text = await self.req.text()




def expect(cls: type[Request]):
    def wraps(f):
        sig = inspect.signature(f)
        argnames = sig.parameters.keys()

        symdiff = set(cls._fieldnames) ^ set(argnames)
        if symdiff:
            raise TypeError(f"Parameter mismatch in '{f.__name__}': {', '.join(symdiff)}")

        @functools.wraps(f)
        async def wrapper(req: aiohttp.web.Request):
            inst = cls(req)
            await inst._prepare()
            return await f(**inst._fields)

        return wrapper
    return wraps
