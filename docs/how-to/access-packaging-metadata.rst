.. _access-packaging-metadata:

=================================================
Accessing Briefcase packaging metadata at runtime
=================================================

When Briefcase installs your app, it adds a `PEP566
<https://www.python.org/dev/peps/pep-0566/>`_ metadata file containing
information about your app, and Briefcase itself. You can retrieve this
information at runtime using importlib::

    import sys
    try:
        from importlib import metadata as importlib_metadata
    except ImportError:
        # Backwards compatibility - importlib.metadata was added in Python 3.8
        import importlib_metadata

    app_module = sys.modules['__main__'].__package__
    metadata = importlib_metadata.metadata(app_module)

    for tag, value in metadata.items():
        print(f'{tag}: {value}')

Executing the above in the sample app from the `Beeware Tutorial
<https://docs.beeware.org/en/latest/tutorial/tutorial-1.html/>`_ will print::

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

Most of these tags display information about your app, corresponding to the
values in the app's ``pyproject.toml`` file. In addition:

    * **Metadata-Version** - Indicates the syntax version of the metadata file
      itself (as defined in `PEP566
      <https://www.python.org/dev/peps/pep-0566/>`_).
    * **Briefcase-Version** - Indicates the version of Briefcase used to
      install it.