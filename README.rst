Ponty: async HTTP server for Python
===================================


Ponty is a simple wrapper on `aiohttp <https://github.com/aio-libs/aiohttp>`__.
It is primarily oriented around building JSON APIs.

.. image:: https://badge.fury.io/py/ponty.svg
   :target: https://pypi.org/project/ponty
   :alt: Latest PyPI package version

.. image:: https://readthedocs.org/projects/ponty/badge/?version=latest
   :target: https://ponty.readthedocs.io/
   :alt: Latest Read The Docs

.. image:: https://img.shields.io/pypi/dm/ponty
   :target: https://pypistats.org/packages/ponty
   :alt: Downloads count



Documentation
=============

https://ponty.readthedocs.io/



Getting Started
===============


Hello World
-----------

.. code-block:: python

    from ponty import (
        expect,
        get, 
        render_json,
        Request, 
        startmeup, 
        StringRouteParameter,
    )


    class Req(Request):

      name = StringRouteParameter()


    @get(f"/hello/{Req.name}")
    @expect(Req)
    @render_json
    async def handler(name: str):
        return {"greeting": f"hi {name}!"}


    if __name__ == "__main__":
        startmeup(port=8000)



Requirements
============

- Python >= 3.8
- aiohttp_
- jsonschema_
- typing-extensions_

.. _aiohttp: https://pypi.org/project/aiohttp/
.. _jsonschema: https://pypi.org/project/jsonschema/
.. _typing-extensions: https://pypi.org/project/typing-extensions/
