===
dev
===

Run the application in developer mode.

Usage
=====

To run the app, run::

    $ briefcase dev

The first time the application runs in developer mode, any requirements listed
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

``-r`` / ``--update-requirements``
----------------------------------

Update application requirements.

``--no-run``
------------
Do not run the application; only install application requirements.

``--test``
----------

Run the test suite in the development environment.
