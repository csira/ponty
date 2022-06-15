import asyncio
from contextlib import asynccontextmanager
import typing

import aiohttp

from ponty.http.go import Provider
from ponty.registry import Registry


_registry = Registry[tuple[asyncio.Semaphore, aiohttp.ClientSession]]()


def http_client_provider(
    *,
    name: str,
    timeout: int = 5,
    concurrency: int = 100,
    headers: dict[str, typing.Any] = None,
    cookies: dict[str, typing.Any] = None,
    **kw
) -> Provider:

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
async def lease_http_client(name: str) -> typing.AsyncIterator[aiohttp.ClientSession]:
    sem, sess = _registry.get(name)
    async with sem:
        yield sess
