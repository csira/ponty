import functools
import inspect
import typing
import warnings

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
            self._json = await self.req.json()

        if self._extract_text:
            self._text = await self.req.text()




def expect(cls: type[Request], *, mimetype: str = None):
    def wraps(f):
        sig = inspect.signature(f)
        argnames = sig.parameters.keys()

        symdiff = set(cls._fieldnames) ^ set(argnames)
        if symdiff:
            raise TypeError(f"Parameter mismatch in '{f.__name__}': {', '.join(symdiff)}")

        if cls._extract_json:
            if mimetype is not None and mimetype != "application/json":
                warnings.warn(f"handler '{f.__name__}' expects a json payload but mimetype '{mimetype}' is expected")

        @functools.wraps(f)
        async def wrapper(req: aiohttp.web.Request):
            if mimetype:
                if mimetype not in req.headers["content-type"]:
                    raise aiohttp.web.HTTPUnsupportedMediaType

            inst = cls(req)
            await inst._prepare()
            return await f(**inst._fields)

        return wrapper
    return wraps
