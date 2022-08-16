Reference
=========


.. autofunction:: ponty.startmeup



Routes
------

Ponty relies on decorator-style routing.

It automatically manages a route table under the hood,
so it's sufficient to simply wrap your handlers like so:

.. code-block:: python

    @get("/hello")
    @render_json
    async def handler(_):
        return {"greeting": "hello world"}

Ponty makes no effort to intercept the 
`aiohttp.web.Request <https://docs.aiohttp.org/en/latest/web_reference.html#aiohttp.web.Request>`__
instance provided by `aiohttp`.
It does, however, provide a :class:`Request <ponty.Request>` class of its own to simplify processing.

Ponty handlers may return 
`aiohttp.web.Response <https://docs.aiohttp.org/en/latest/web_reference.html#aiohttp.web.Response>`__
instances directly, or they may take advantage of utilities such as
:func:`ponty.render_json` or :func:`ponty.raise_status`.


.. autodecorator:: ponty.route


.. decorator:: ponty.get(path, **kw)

   Register a GET handler.
   See :py:func:`route` for parameter information.


.. decorator:: ponty.post(path, **kw)

   Register a POST handler.
   See :py:func:`route` for parameter information.


.. decorator:: ponty.put(path, **kw)

   Register a PUT handler.
   See :py:func:`route` for parameter information.


.. decorator:: ponty.delete(path, **kw)

   Register a DELETE handler.
   See :py:func:`route` for parameter information.


.. decorator:: ponty.patch(path, **kw)

   Register a PATCH handler.
   See :py:func:`route` for parameter information.


.. autofunction:: ponty.route_iter



Request
-------

.. autoclass:: ponty.Request
.. autodecorator:: ponty.expect


For example,

.. code-block:: python

    from ponty import (
        expect,
        get,
        render_json,
        Request,
        StringRouteParameter,
    )


    class HelloReq(Request):

        name = StringRouteParameter()


    @get(f"/hello/{HelloReq.name}")  # evaluates to "/hello/{name:\w+}"
    @expect(HelloReq)
    @render_json
    async def greet(name: str):
        return {"greeting": f"hello, {name}!"}


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
    < Date: Thu, 11 Aug 2022 02:58:44 GMT
    < Server: Python/3.9 aiohttp/3.7.3
    <
    {
        "data": {
            "greeting": "hello you!"
        },
        "elapsed": 0,
        "now": 1660186724077
    }



.. _Descriptors:

Descriptors
***********

Descriptors are stored as class variables on another class.
Within the Ponty context, the containing class is :class:`ponty.Request`.

The following descriptors implement rules for extracting and processing 
components of the HTTP request. 
In conjunction with :func:`ponty.expect`, 
request descriptors are parameterized directly into the decorated handler.
(Descriptor names are reused as parameter names.)


Route Parameters
^^^^^^^^^^^^^^^^

.. autoclass:: ponty.RouteParameter
.. autoclass:: ponty.PosIntRouteParameter
.. autoclass:: ponty.StringRouteParameter


Query Parameters
^^^^^^^^^^^^^^^^
.. autoclass:: ponty.QueryParameter
.. autoclass:: ponty.QueryParameterEnum


Request Body
^^^^^^^^^^^^
.. autoclass:: ponty.TextBody
.. autoclass:: ponty.JsonBody
.. autoclass:: ponty.ValidatedJsonBody(*, filepath=None)
.. autoclass:: ponty.ParsedJsonBody


Request Headers
^^^^^^^^^^^^^^^
.. autoclass:: ponty.Header
.. autoclass:: ponty.ContentLength
.. autoclass:: ponty.ContentType


Other
^^^^^

.. autoclass:: ponty.AIOHttpReq
.. autoclass:: ponty.Cookie



Schema Validation
*****************

.. autoclass:: ponty.Annotation
.. autofunction:: ponty.dataclass_to_jsonschema



Response
--------


.. autodecorator:: ponty.render_json
.. autofunction:: ponty.raise_status


HTTP Errors
***********

.. autoexception:: ponty.PontyError
   :members:

.. autoexception:: ponty.DoesNotExist
.. autoexception:: ponty.ValidationError




.. _Providers:

Providers
---------

Providers manage shared assets, and are Ponty's way of tapping into
`aiohttp.web.Application.cleanup_ctx <https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.Application.cleanup_ctx>`_
for startup/cleanup handling.

Providers are asynchronous generators that take a single argument, an instance of
`aiohttp.web.Application <https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.Application>`_.
Code before the `yield` initializes the asset during startup, 
while code after the `yield` runs during teardown.

Providers must be passed to :py:func:`ponty.startmeup` for proper handling.


.. autofunction:: ponty.http_client_provider
.. autofunction:: ponty.lease_http_client



Utils
-----

.. autodecorator:: ponty.retry
