Quickstart
==========

To install Briefcase, run::

    $ pip install briefcase

Then, add a ``pyproject.toml`` file to the root of your project (if you
don't already have one), and add the following content::

    [build-system]
    requires = ["briefcase"]

    [tool.briefcase]
    project_name = "My project"
    bundle = "com.example"
    version = "0.1"

    [tool.briefcase.app.myapp]
    formal_name = "My App"
    description = "My first Briefcase App"
    sources = ['src/myapp']
    requires = ['...']

Replace the references to "myapp" with your own app name, update `sources`
to point at the locations that contain your code, and add any dependencies
to the ``requires`` list.

Your first build
----------------

Then, you can invoke ``briefcase``::

    $ briefcase create
    $ briefcase build
    $ briefcase run

This will create the default output format for your current computer's operating
system, build the app, and run the application.

Building for another platform
-----------------------------

If you want to target a different platform, you can pass that platform name
as an argument. For example, to create an iOS app, run::

    $ briefcase create iOS
    $ briefcase build iOS
    $ briefcase run iOS

.. admonition:: Build tool dependencies

    Building for some platforms depends on the build tools for the platform
    you're targetting being available on the platform you're using. For
    example, you will only be able to create iOS applications on macOS.
    Briefcase will check for any required tools, and will report an error if
    the platform you're targetting is not supported.

Updating your code
------------------

While you're developing an application, you may need to rapidly iterate on the
code, making small changes and then re-building. To repackage the code in your
application, run::

    $ briefcase update

then rebuild your app. The ``update`` command also accepts a `-d` command if
you need to update your dependencies, and a ``-r`` if you need to update
application resources (such as icons and splash images).

Alternatively, if you want to repackage your application's code and
immediately re-run the app, you can pass ``-u`` to the ``run`` command::

    $ briefcase run -u
