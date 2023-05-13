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
platform:

.. code-block:: console

    $ briefcase build

To build the application for a different platform:

.. code-block:: console

    $ briefcase build <platform>

To build the application for a specific output format:

.. code-block:: console

    $ briefcase build <platform> <output format>

.. admonition:: Build tool requirements

    Building for some platforms depends on the build tools for the platform
    you're targeting being available on the platform you're using. For
    example, you will only be able to create iOS applications on macOS.
    Briefcase will check for any required tools, and will report an error if
    the platform you're targeting is not supported.

Options
=======

The following options can be provided at the command line.

``-u`` / ``--update``
---------------------

Update the application's source code before building. Equivalent to running:

.. code-block:: console

    $ briefcase update
    $ briefcase build

``-r`` / ``--update-requirements``
----------------------------------

Update application requirements before building. Equivalent to running:

.. code-block:: console

    $ briefcase update -r
    $ briefcase build

``--update-resources``
----------------------

Update application resources (e.g., icons and splash screens) before building.
Equivalent to running:

.. code-block:: console

    $ briefcase update --update-resources
    $ briefcase build

``--update-support``
----------------------

Update application support package before building. Equivalent to running:

.. code-block:: console

    $ briefcase update --update-resources
    $ briefcase build

``--test``
----------

Build the app in test mode in the bundled app environment. Running ``build
--test`` will also cause an update to ensure that the packaged application
contains the current test code. To prevent this update, use the ``--no-update``
option.

If you have previously run the app in "normal" mode, you may need to pass ``-r``
/ ``--update-requirements`` the first time you build in test mode to ensure that
your testing requirements are present in the test app.

``--no-update``
---------------

Prevent the automated update of app code that is performed when specifying by
the ``--test`` option.
