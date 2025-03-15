===
run
===

Starts the application, using the packaged version of the application code.
By default, targets the current platform's default output format.

If the output format is an executable (e.g., a macOS .app file), the ``run``
command will start that executable. If the output is an installer, ``run`` will
attempt to replicate as much as possible of the runtime environment that would
be installed, but will not actually install the app. For example, on Windows,
``run`` will use the interpreter that will be included in the installer, and
the versions of code and requirements that will be installed, but *won't* run
the installer to produce Start Menu items, registry records, etc.

Test mode
---------

The ``run`` command can also be used to execute your app's test suite, in the
packaged environment (e.g., on the iOS simulator, or from within a Linux
Flatpak). When running in test mode (using the ``--test`` option), a different
entry point will be used for the app: if your app is contained in a Python
module named ``myapp``, test mode will attempt to launch ``tests.myapp``. Your
app is responsible for providing the logic to discover and start the test suite.

The code for your test suite can specified using the ``test_sources`` setting;
test-specific requirements can be specified with ``test_requires``. Test sources
and requirements will only be included in your app when running in test mode.

Briefcase will monitor the log output of the test suite, looking for the output
corresponding to test suite completion. Briefcase has built-in support for
`pytest <https://docs.pytest.org/en/latest>`__ and `unittest
<https://docs.python.org/3/library/unittest.html>`__ test suites; support for
other test frameworks can be added using the ``test_success_regex`` and
``test_failure_regex`` settings.

Debug mode
----------

The debug mode can be used to (remote) debug an bundled app. The debugger to
use can be configured via ``pyproject.toml`` an can then be activated through
``run --debug``.

This is incredible useful when developing an iOS or Android app that can't be
debugged via ``briefcase dev``.

To debug an bundled app you need a socket connection from your host system to
the device running your bundled app. Depending on the debugger selected the
bundled app is either a socket server or socket client.

This feature needs to inject some code into your app to create the socket
connection. So you have to add ``import __briefcase_startup__`` to your
``__main__.py`` to get this running.
TODO: Better use .pth Files for this, so no modification of the app is needed.
      But using this currently creates an import error on android...

Some debuggers (like ``debugpy``) also support the mapping of the source code
from your bundled app to your local copy of the apps source code in the
``build`` folder.

The configuration is done via ``pyproject.toml``:

- ``debugger``:
   - ``pdb`` (default):
        This is used for debugging via console.
        Currently it only supports ``debgger_mode=server``.
        It creates a socket server that streams all stdout/stderr/stdin to
        the host PC. The host PC can connect to it via:
            - ``telnet localhost 5678``
            - ``nc -C localhost 5678``
            - ``socat readline tcp:localhost:5678``.
        The app will start after the connection is established.
   - ``debugpy``:
        This is used for debugging via VSCode:
            - If ``debgger_mode=server``: The bundled app creates an socket server an VSCode can connect to it.
            - If ``debgger_mode=client``: This is used for debugging via VSCode. VSCode has to create an socket server and the bundled app connects to VSCode.
   - ``debugpy-client``:
        This is used for debugging via VSCode. VSCode has to create an socket server and the bundled app connects to VSCode.
- ``debugger_mode``:
    - ``server`` (default):
        The bundled app creates an socket server and the host system connects to it.
    - ``client``:
        The bundled app creates an socket client and the host system creates an socket server.
    Note, that not all debuggers support all modes.
- ``debugger_ip``:
    Specifies the IP of the socket connection (defaults to ``localhost``)
- ``debugger_port``:
    Specifies the Port of the socket connection (defaults to ``5678``)


Usage
=====

To run your application on the current platform's default output format:

.. code-block:: console

    $ briefcase run

To run your application for a different platform:

.. code-block:: console

    $ briefcase run <platform>

To run your application using a specific output format:

.. code-block:: console

    $ briefcase run <platform> <output format>

Options
=======

The following options can be provided at the command line.

``-a <app name>`` / ``--app <app name``
---------------------------------------

Run a specific application target in your project. This argument is only
required if your project contains more than one application target. The app
name specified should be the machine-readable package name for the app.

``-u`` / ``--update``
---------------------

Update the application's source code before running. Equivalent to running:

.. code-block:: console

    $ briefcase update
    $ briefcase build
    $ briefcase run

``-r`` / ``--update-requirements``
----------------------------------

Update application requirements before running. Equivalent to running:

.. code-block:: console

    $ briefcase update -r
    $ briefcase build
    $ briefcase run

``--update-resources``
----------------------

Update application resources such as icons before running. Equivalent to
running:

.. code-block:: console

    $ briefcase update --update-resources
    $ briefcase build
    $ briefcase run

``--update-support``
--------------------

Update application support package before running. Equivalent to running:

.. code-block:: console

    $ briefcase update --update-support
    $ briefcase build
    $ briefcase run

``--update-stub``
-----------------

Update stub binary before running. Equivalent to running:

.. code-block:: console

    $ briefcase update --update-stub
    $ briefcase build
    $ briefcase run

``--test``
----------

Run the app in test mode in the bundled app environment. Running ``run --test``
will also cause an update and build to ensure that the packaged application
contains the most recent test code. To prevent this update and build, use the
``--no-update`` option.

``--no-update``
---------------

Prevent the automated update and build of app code that is performed when
specifying by the ``--test`` option.

``--debug``
----------

Run the app in debug mode in the bundled app environment. This option can be used
standalone or in combination with the test mode ``run --test --debug``.

On Android this also forwards the ``debugger_port`` from the android device to the host pc via adb.

Passthrough arguments
---------------------

If you want to pass any arguments to your app's command line, you can specify them
using the ``--`` marker to separate Briefcase's arguments from your app's arguments.
For example:

.. code-block:: console

    briefcase run -- --wiggle --test

will run the app in normal mode, passing the ``--wiggle`` and ``--test`` flags to
the app's command line. The app will *not* run in *Briefcase's* test mode; the
``--test`` flag will be left for your own app to interpret.
