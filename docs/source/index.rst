.. Ponty documentation master file, created by
   sphinx-quickstart on Wed Jul 27 22:04:11 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Ponty's documentation!
=================================

Asynchronous HTTP server & related utils for Python.

Ponty is an opinionated wrapper on `aiohttp <https://github.com/aio-libs/aiohttp>`_.
It is primarily oriented around building JSON APIs,
but does not interfere with using advanced aiohttp features directly.

Current version is |release|.

.. _GitHub: https://github.com/csira/ponty


Installation
============

.. code-block:: bash

    $ pip install ponty


Example
=======

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
        return {"greeting": f"hello {name}"}

        
    if __name__ == "__main__":
        startmeup(port=8080)


.. code-block:: bash

    $ curl localhost:8080/hello/you -v | python -m json.tool
    > GET /hello/you HTTP/1.1
    > Host: localhost:8080
    > User-Agent: curl/7.64.1
    > Accept: */*
    >
    < HTTP/1.1 200 OK
    < Content-Type: application/json; charset=utf-8
    < Content-Length: 72
    < Date: Tue, 02 Aug 2022 13:53:11 GMT
    < Server: Python/3.9 aiohttp/3.7.3
    <
    {
        "data": {
            "greeting": "hello you!"
        },
        "elapsed": 0,
        "now": 1659448391571
    }


Source
======

Ponty is hosted on GitHub_.

Please feel free to file an issue on the 
`bug tracker <https://github.com/csira/ponty/issues>`_ 
if you have found a bug, would like to improve the documentation,
or have suggestions. 


Contents
========

.. toctree::
   :maxdepth: 2
   :name: maintoc

   reference


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
