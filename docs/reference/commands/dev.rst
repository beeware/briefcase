===
dev
===

Run the application in developer mode.

Usage
=====

To run the app, run::

    $ briefcase dev

The first time the application runs in developer mode, any dependencies listed
in a `requires` configuration item in `pyproject.toml` will be installed into
the current environment.

Options
=======

The following options can be provided at the command line.

``-a <app name>`` / ``--app <app name``
---------------------------------------

Run a specific application target in your project. This argument is only
required if your project contains more than one application target. The app
name specified should be the machine-readable package name for the app.

``-d`` / ``--update-dependencies``
----------------------------------

Update application dependencies.

``--no-run``
------------
Do not run the application and only install application dependencies.
