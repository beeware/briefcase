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
the versions of code and dependencies that will be installed, but *won't* run
the installer to produce Start Menu items, registry records, etc.

Usage
=====

To run your application on the current platform's default output format::

    $ briefcase run

To run your application for a different platform::

    $ briefcase run <platform>

To run your application using a specific output format::

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

Update the application's source code before running. Equivalent to running::

    $ briefcase update
    $ briefcase run
