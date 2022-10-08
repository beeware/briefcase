.. _access-packaging-metadata:

=================================================
Accessing Briefcase packaging metadata at runtime
=================================================

When Briefcase installs your app, it adds a `PEP566
<https://www.python.org/dev/peps/pep-0566/>`_ metadata file containing
information about your app, and Briefcase itself. You can retrieve this
information at runtime using the `Python builtin library 'importlib.metadata'
<https://docs.python.org/3/library/importlib.metadata.html>`__.
``importlib.metadata`` was added in Python 3.8; however, it has been backported
and published on PyPI as `'importlib_metadata'
<https://pypi.org/project/importlib-metadata/>`__ for older versions of Python.

To access application metadata at runtime, you can use the following code::

    import sys
    try:
        from importlib import metadata as importlib_metadata
    except ImportError:
        # Backwards compatibility - importlib.metadata was added in Python 3.8
        import importlib_metadata

    # Find the name of the module that was used to start the app
    app_module = sys.modules['__main__'].__package__
    # Retrieve the app's metadata
    metadata = importlib_metadata.metadata(app_module)

The ``metadata`` returned by this code will be a dictionary-like object that
contains the following identifying keys:

  * **Metadata-Version** - The syntax version of the metadata file itself (as
    defined in `PEP566 <https://www.python.org/dev/peps/pep-0566/>`_).

  * **Briefcase-Version** - The version of Briefcase used to package the app.
    The existence of this key in app metadata can be used to identify if your
    application code is running in a Briecase container; it will only exist if
    the app has been packaged by Briefcase.

It will also have the following keys, derived from your application's
``pyproject.toml`` configuration:

  * **Name** - ``app_name``
  * **Formal-Name** - ``formal_name``
  * **App-ID** - ``bundle`` and ``app_name``, joined with a ``.``
  * **Version** - ``version``
  * **Summary** - ``description``

The metadata may also contain the following keys, if they have been defined
in your app's ``pyproject.toml`` configuration:

  * **Home-page** - ``url``
  * **Author** - ``author``
  * **Author-email** - ``author_email``

For example, the metadata for the app constructed by the `Beeware Tutorial
<https://docs.beeware.org/en/latest/tutorial/tutorial-1.html>`_ would
contain::

    Metadata-Version: 2.1
    Briefcase-Version: 0.3.1
    Name: helloworld
    Formal-Name: Hello World
    App-ID: com.example.helloworld
    Version: 0.0.1
    Home-page: https://example.com/helloworld
    Author: Jane Developer
    Author-email: jane@example.com
    Summary: My first application
