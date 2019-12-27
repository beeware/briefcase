=======
package
=======

Compile/build an application installer. By default, targets the current
platform's default output format.

This will produce an installable artefact.

Usage
=====

To build an installer of the default output format for the current platform::

    $ briefcase package

To build an installer for a different platform::

    $ briefcase package <platform>

To build an installer for a specific output format::

    $ briefcase package <platform> <output format>

.. admonition:: Packaging tool dependencies

    Building installers for some platforms depends on the build tools for the
    platform you're targetting being available on the platform you're using.
    For example, you will only be able to create iOS applications on macOS.
    Briefcase will check for any required tools, and will report an error if
    the platform you're targetting is not supported.

Options
=======

The following options can be provided at the command line.

``-u`` / ``--update``
---------------------

Update and recompile the application's code before running. Equivalent to
running::

    $ briefcase update
    $ briefcase package
