import aiohttp.web


class DefaultMixin:

    def __init__(self, *, required: bool = False, default: str = ""):
        if required and default:
            raise TypeError

        self._required = required
        self._default = default

    def get_default(self):
        if self._required:
            raise aiohttp.web.HTTPBadRequest
        return self._default
