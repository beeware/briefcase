=======
package
=======

Compile/build an application installer. By default, targets the current
platform's default output format.

This will produce an installable artefact.

Usage
=====

To build an installer of the default output format for the current platform:

.. code-block:: console

    $ briefcase package

To build an installer for a different platform:

.. code-block:: console

    $ briefcase package <platform>

To build an installer for a specific output format:

.. code-block:: console

    $ briefcase package <platform> <output format>

.. admonition:: Packaging tool requirements

    Building installers for some platforms depends on the build tools for the
    platform you're targeting being available on the platform you're using.
    For example, you will only be able to create iOS applications on macOS.
    Briefcase will check for any required tools, and will report an error if
    the platform you're targeting is not supported.

Options
=======

The following options can be provided at the command line.

``-u`` / ``--update``
---------------------

Update and recompile the application's code before running. Equivalent to
running:

.. code-block:: console

    $ briefcase update
    $ briefcase package

``-p <format>``, ``--packaging-format <format>``
------------------------------------------------

The format to use for packaging. The available packaging formats are platform
dependent.

``--adhoc-sign``
----------------

Perform the bare minimum signing that will result in a app that can run on your
local machine. This may result in no signing, or signing with an ad-hoc signing
identity. The ``--adhoc-sign`` option may be useful during development and
testing. However, care should be taken using this option for release artefacts,
as it may not be possible to distribute an ad-hoc signed app to others.

``-i <identity>`` / ``--identity <identity>``
---------------------------------------------

The :doc:`code signing identity </how-to/code-signing/index>` to use when
signing the app.
