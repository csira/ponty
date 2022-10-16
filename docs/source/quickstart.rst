Quickstart
==========


Keen to get moving?
These tutorials will walk you through some common Ponty concepts.


.. contents::
   :local:
   :depth: 2



1. A basic application
----------------------

A simple example demonstrates starting the server
and serving a static JSON payload from a static URI.

The endpoint will be served at
`http://0.0.0.0:8000/hello <http://0.0.0.0:8000/hello>`__.

.. literalinclude:: tutorial/t1.py


Save in ``t1.py`` and run with:

.. code-block:: bash

    $ python t1.py


Which displays:

.. code-block:: bash

    serving:
    GET /hello

    DEBUG:asyncio:Using selector: KqueueSelector
    ======== Running on http://0.0.0.0:8000 ========
    (Press CTRL+C to quit)


From this, you can conclude:
  * one method/route pair, `GET /hello`, has been mounted
  * the server is listening on 0.0.0.0:8000
  * the server will shutdown if it receives a SIGINT_


Some things to note about the code:
  * Ponty uses decorator-style routing.
    ``@get("/hello")`` indicates this handler will only be invoked
    by HTTP requests specifying a ``GET`` method to ``/hello``
  * Request handlers must be coroutines, hence they must use ``async``
  * Ponty is built on aiohttp_, and deliberately does not interfere with
    direct use of advanced aiohttp features.
    Hence, by default, each Ponty handler accepts an
    `aiohttp.Request` instance as its only argument and must return an
    `aiohttp.Response` instance.
    (Under the hood, most Ponty code simply intercepts
    and repackages these.)

    * In simple cases such as this, where we don't need additional data
      from the request, it's sufficient to stub out the
      `aiohttp.Request` parameter with a wildcard_.
      (Later we'll see how to use the `Request` ergonomically.)
    * Ponty is primarily oriented around the development of JSON APIs.
      For an endpoint returning JSON, use the ``render_json`` decorator
      on a coroutine returning a JSON-serializable Python object to
      automatically build the `aiohttp.Response` (i.e. serialize the data,
      set the body, and set the content-type & contenth-length headers). [#dc]_

  * ``startmeup`` is the main entrypoint for an application.
    The `port` argument is required



2. Dynamic URIs
---------------

In many applications, URIs contain valuable information (e.g. a record id).
Let's stand up an endpoint that, given a person's name, greets them:

.. literalinclude:: tutorial/t2.py


New details:
  * The ``HelloReq`` class inherits :class:`Request <ponty.Request>`,
    the Ponty base class responsible for applying
    a sequence of pre-processing rules to the HTTP request

    * ``name = StringRouteParameter()`` is one of those rules.
      It indicates we expect a dynamic URI component,
      which will be processed as a string,
      and which we're choosing to call `name`

  * Note the URI, ``f"/hello/{HelloReq.name}"``,
    an f-string which references ``name``.
    When invoked from the class,
    the ``name`` descriptor evaluates to the expression
    required for path matching (i.e., interpolated, ``/hello/{name:\w+}``)

    * Hence, ``@get("/hello/{name:\w+}")`` matches on HTTP requests with
      method GET, where the URI matches ``^/hello/(\w+)$``:

      .. code-block:: python

          >>> import re
          >>> match = re.match("^/hello/(\w+)$", "/hello/world")
          >>> match.groups()
          ('world',)


  * :func:`expect <ponty.expect>` connects ``HelloReq`` with the handler function

    * at compile time, :func:`expect <ponty.expect>` validates
      the bijection between the parameter list
      and the sequence of rules

    * at runtime, :func:`expect <ponty.expect>` captures the request,
      runs it through each rule in ``HelloReq``,
      then parameterizes each result into the decorated handler.
      (In this case, it binds ``name <- 'world'``)

    * note now ``async def handler(name: str)`` is conveniently parameterized
      (and typed)



3. Validating a request body
----------------------------

Many APIs react to data submitted by their clients.
Ponty favors validating data as early as possible -
this approach reduces the odds of a partial transaction rollback
and reduces boilerplate.

Now let's create an endpoint that updates a user's profile:

.. literalinclude:: tutorial/t3.py


New details:
  * This time,
    our :class:`Request <ponty.Request>` subclass ``UpdateProfileReq``
    uses :class:`PosIntRouteParameter <ponty.PosIntRouteParamter>`
    to capture the dynamic URI component.
    :class:`PosIntRouteParameter <ponty.PosIntRouteParamter>`
    matches on ``\d+`` *and* casts the match to an integer

  * ``UpdateProfileReq`` uses
    :class:`ParsedJsonBody <ponty.ParsedJsonBody>` as well,
    which has two effects:

    * At compile-time, a jsonschema validator is auto-generated
      from the annotations in the given dataclass [#anno]_ [#anno2]_

      * When the request is captured, the body is validated against
        that jsonschema.
        If validation fails, a 400 Bad Request is raised immediately;
        ``handler`` is not reached

    * Once validated, the request body is marshalled into an instance
      of the dataclass and passed to the handler.
      Since we called the descriptor `body`,
      it takes that name in the parameter list as well

  * :func:`raise_status <ponty.raise_status>` allows you
    to control additional aspects of the response

    * HTTP status code is a required argument

    * headers and request body (``text`` for the raw string,
      ``body`` for a JSON-serializable Python object) are optional

    * In this case we're using ``Result`` to enumerate the possible status codes,
      trusting ``update_profile`` to return the right one,
      and then using ``raise_status(result.value)``
      to build the HTTP response with that status code


A few curls:

.. code-block:: bash
    :caption: success (200)
    :emphasize-lines: 13

    $ curl localhost:8000/user/1 \
        -X PUT \
        -H "content-type:application/json" \
        -d '{"given_name": "John", "surname": "Cleese", "email": "monty@python.org"}' \
        -v
    > PUT /user/1 HTTP/1.1
    > Host: localhost:8000
    > User-Agent: curl/7.79.1
    > Accept: */*
    > content-type:application/json
    > Content-Length: 72
    >
    < HTTP/1.1 200 OK
    < Content-Type: text/plain; charset=utf-8
    < Content-Length: 7
    < Date: Fri, 14 Oct 2022 02:51:15 GMT
    < Server: Python/3.9 aiohttp/3.7.3
    <
    200: OK


.. code-block:: bash
    :caption: missing the "email" parameter (400)
    :emphasize-lines: 4,13,19

    $ curl localhost:8000/user/1 \
        -X PUT \
        -H "content-type:application/json" \
        -d '{"given_name": "John", "surname": "Cleese"}' \
        -v
    > PUT /user/1 HTTP/1.1
    > Host: localhost:8000
    > User-Agent: curl/7.79.1
    > Accept: */*
    > content-type:application/json
    > Content-Length: 43
    >
    < HTTP/1.1 400 Bad Request
    < Content-Type: text/plain; charset=utf-8
    < Content-Length: 30
    < Date: Fri, 14 Oct 2022 02:14:17 GMT
    < Server: Python/3.9 aiohttp/3.7.3
    <
    'email' is a required property


.. code-block:: bash
    :caption: non-integer ``user_id`` (404)
    :emphasize-lines: 1,7

    $ curl -X PUT localhost:8000/user/abc -v
    > PUT /user/abc HTTP/1.1
    > Host: localhost:8000
    > User-Agent: curl/7.79.1
    > Accept: */*
    >
    < HTTP/1.1 404 Not Found
    < Content-Type: text/plain; charset=utf-8
    < Content-Length: 14
    < Date: Fri, 14 Oct 2022 02:02:04 GMT
    < Server: Python/3.9 aiohttp/3.7.3
    <
    404: Not Found



.. _SIGINT: https://docs.python.org/3/library/signal.html#signal.SIGINT
.. _aiohttp: https://github.com/aio-libs/aiohttp
.. _asdict: https://docs.python.org/3/library/dataclasses.html#dataclasses.asdict
.. _wildcard: https://docs.python.org/3/reference/lexical_analysis.html#reserved-classes-of-identifiers



----------


.. rubric:: Footnotes

.. [#dc] Hot tip: dataclasses are not JSON-serializable,
   but can be turned into a dictionary trivially with `asdict`_.

.. [#anno] This is the only case where Ponty allows runtime inspection
   of type annotations. Note it is possible to bypass this behavior by using
   :class:`ParsedJsonBody <ponty.ParsedJsonBody>`'s ``filepath`` argument
   instead.

.. [#anno2] See :func:`ponty.dataclass_to_jsonschema`
   for details and examples.
