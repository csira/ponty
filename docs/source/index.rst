.. Ponty documentation master file, created by
   sphinx-quickstart on Wed Jul 27 22:04:11 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Ponty's documentation!
=================================

Asynchronous HTTP server & related utils for Python.

Ponty is an opinionated wrapper on `aiohttp <https://github.com/aio-libs/aiohttp>`__.
It is primarily oriented around building JSON APIs.

We like static analysis, early validation, and minimal sorcery,
so the design of the package is built with those things in mind.

* early validation.
  With inputs validated as early as possible,
  the surface area for security issues can be reduced
  and the odds of a partial transaction rollback can be minimized.
  Additionally, by completing validation in a consolidated pass
  before reaching the request handler,
  parameter annotations can be accurate
  and boilerplate all but disappears.

* static analysis.
  Ponty avoids runtime inspection of type annotations. [#anno]_ [#anno2]_

* explicit over implicit.
  Enumerating request-processing rules means you get what you want -
  no more no less.

Here we go.


Current version is |release|.

*Doc improvements ongoing. Contributions are welcome!*


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
            "greeting": "hello you"
        },
        "elapsed": 0,
        "now": 1659448391571
    }


Source
======

Ponty is hosted on GitHub_.

Please feel free to open a
`PR <https://github.com/csira/ponty/pulls>`__
or file an issue on the
`bug tracker <https://github.com/csira/ponty/issues>`__
if you have found a bug, would like to improve the documentation,
or have a suggestion.


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


----------


.. rubric:: Footnotes

.. [#anno] Keeping with the spirit of annotations having no runtime behavior
   (`PEP-484 <https://peps.python.org/pep-0484/#compatibility-with-other-uses-of-function-annotations>`__),
   and in order to steer clear of the uncertain future of
   `PEP-649 <https://peps.python.org/pep-0649/>`__,
   Ponty assumes ``from __future__ import annotations``
   (`PEP-563 <https://peps.python.org/pep-0563/>`__)
   will eventually become the default.
   Hence, perhaps at the expense of brevity, Ponty does not use type hints
   for validation or type conversion. [#anno2]_

.. [#anno2] One exception: Ponty will automatically turn a dataclass
   into a jsonschema validator if you ask it to.
   See :class:`ParsedJsonBody <ponty.ParsedJsonBody>`
   (which calls :func:`dataclass_to_jsonschema <ponty.dataclass_to_jsonschema>`)
