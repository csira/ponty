import asyncio
from contextlib import asynccontextmanager
import typing

import aiohttp

from ponty.http.go import Provider
from ponty.registry import Registry


_registry = Registry[tuple[asyncio.Semaphore, aiohttp.ClientSession]]()
_defaultname: typing.Final[str] = "_default"


def http_client_provider(
    *,
    name: str = _defaultname,
    timeout: int = 5,
    concurrency: int = 100,
    headers: dict[str, typing.Any] = None,
    cookies: dict[str, typing.Any] = None,
    **kw
) -> Provider:
    """Builds an HTTP Client Session provider.

    Wraps `aiohttp.ClientSession <https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession>`_.

    :param name: unique name, used by :func:`lease_http_client`
    :param timeout: total timeout for the complete operation, in seconds
    :param concurrency: maximum number of concurrent requests
    :param headers: headers to send with each request
    :param cookies: cookies to send with each request
    :param kw: additional parameters, specified `here <https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession>`__
    :return: a provider, which should be passed to :func:`startmeup`


    .. code-block:: python

        startmeup(
            port=8080,
            providers=(
                http_client_provider(
                    timeout=30,
                    concurrency=10,
                ),
            ),
        )

    """
    async def provider(_) -> typing.AsyncIterator[None]:
        sem = asyncio.Semaphore(concurrency)
        sess = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout),
            headers=headers,
            cookies=cookies,
            **kw
        )

        _registry.add(name, (sem, sess))

        try:
            yield
        finally:
            await sess.close()
            await asyncio.sleep(0.5)  # sleep a beat to allow underlying connections to close

    return provider


@asynccontextmanager
async def lease_http_client(name: str = _defaultname) -> typing.AsyncIterator[aiohttp.ClientSession]:
    """
    Context manager. Fetch the named http client session, leasing one
    of its request positions or blocking until one becomes available,
    then return it to the pool after the block is exited.

    :param name: see :func:`http_client_provider` parameter ``name``
    :raises KeyError: if the named session was not registered (via :func:`startmeup`)
    :yields: `aiohttp.ClientSession <https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession>`__


    .. code-block:: python

        async with lease_http_client() as sess:
            async with sess.get("https://www.python.org/") as resp:
                html = await resp.text()

    """
    sem, sess = _registry.get(name)
    async with sem:
        yield sess
