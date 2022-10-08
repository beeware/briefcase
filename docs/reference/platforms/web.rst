===
Web
===

When generating a web project, Briefcase produces a static folder of HTML, CSS
and JavaScript resources that can be deployed as a web site. The static web site
is packaged as a ``.zip`` file for distribution.

Although Briefcase provides a ``run`` command that can be used to serve the
website, this web server is provided as a development convenience. **It should
not be used in production**. If you wish to serve your app in production, you
can unzip the ``.zip`` file in the root of any webserver that can serve static
web content.

.. admonition:: Web support is experimental!

    `PyScript <https://pyscript.net>`__ (which forms the base of Briefcase's
    web backend) is a new project; and Toga's web backend is very new. As a
    result this web backend should be considered experimental.

    Regardless of what Python version you run Briefcase with, the app will use
    PyScript's current Python version (as of October 2022, this is 3.10).

    There are also a `number of constraints
    <https://pyodide.org/en/stable/usage/wasm-constraints.html>`__ on what you
    can do in a web environment. Some of these are fundamental constraints on
    the web as a platform; some are known issues with Pyscript and Pyodide as
    runtime environments. You shouldn't expect that arbitrary third-party Python
    packages will "just run" in a web environment.

Icon format
===========

Web projects use a single 32px ``.png`` format icon as the site icon.

Splash Image format
===================

Web projects do not support splash screens or installer images.

Additional options
==================

The following options can be provided at the command line when producing
iOS projects

run
---

``--host <ip or hostname>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The hostname or IP address that the development web server should be bound to.
Defaults to ``localhost``.

``-p <port>`` / ``--port <port>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The port that the development web server should be bound to. Defaults to ``8080``.

``--no-browser``
~~~~~~~~~~~~~~~~

Don't open a web browser after starting the development web server.
