=====
build
=====

Compile/build an application installer. By default, targets the current
platform's default output format.

Usage
=====

To build the application for the default output format for the current
platform::

    $ briefcase build

To build the application for a different platform::

    $ briefcase build <platform>

To build the application for a specific output format::

    $ briefcase build <platform> <output format>

.. admonition:: Build tool dependencies

    Building for some platforms depends on the build tools for the platform
    you're targetting being available on the platform you're using. For
    example, you will only be able to create iOS applications on macOS.
    Briefcase will check for any required tools, and will report an error if
    the platform you're targetting is not supported.
