===
dev
===

Run the application in developer mode.

Usage
=====

To run the app, run:

.. code-block:: console

    $ briefcase dev

The first time the application runs in developer mode, any requirements listed
in a ``requires`` configuration item in ``pyproject.toml`` will be installed into
the current environment.

Options
=======

The following options can be provided at the command line.

``-a <app name>`` / ``--app <app name``
---------------------------------------

Run a specific application target in your project. This argument is only
required if your project contains more than one application target. The app
name specified should be the machine-readable package name for the app.

``-r`` / ``--update-requirements``
----------------------------------

Update application requirements.

``--no-run``
------------
Do not run the application; only install application requirements.

``--test``
----------

Run the test suite in the development environment.

Passthrough arguments
---------------------

If you want to pass any arguments to your app's command line, you can specify them
using the ``--`` marker to separate Briefcase's arguments from your app's arguments.
For example:

.. code-block:: console

    $ briefcase dev -- --wiggle --test

will run the app in normal mode, passing the ``--wiggle`` and ``--test`` flags to
the app's command line. The app will *not* run in *Briefcase's* test mode; the
``--test`` flag will be left for your own app to interpret.
