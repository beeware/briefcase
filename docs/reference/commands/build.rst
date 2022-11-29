=====
build
=====

Compile/build an application. By default, targets the current platform's
default output format.

This will only compile the components necessary to *run* the application. It
won't necessarily result in the generation of an installable artefact.

Usage
=====

To build the application for the default output format for the current
platform::

    $ briefcase build

To build the application for a different platform::

    $ briefcase build <platform>

To build the application for a specific output format::

    $ briefcase build <platform> <output format>

.. admonition:: Build tool requirements

    Building for some platforms depends on the build tools for the platform
    you're targetting being available on the platform you're using. For
    example, you will only be able to create iOS applications on macOS.
    Briefcase will check for any required tools, and will report an error if
    the platform you're targetting is not supported.

Options
=======

The following options can be provided at the command line.

``-u`` / ``--update``
---------------------

Update the application's source code before running. Equivalent to running::

    $ briefcase update
    $ briefcase build

``--test``
----------

Build the app in test mode in the bundled app environment. Running ``build
--test`` forces an update to ensure that the packaged application contains all
the test requirements and code. To prevent this update and build, use
``--no-update``.

``--no-update``
---------------

Prevent the automated update that is performed when specifying by the
``--test`` option. This option should only be required if you need to
build your app on one machine, and run it on another.
