======
create
======

Create a scaffold for an application installer. By default, targets the current
platform's default output format.

Usage
=====

To create a scaffold for the default output format for the current platform:

.. code-block:: console

    $ briefcase create

To create a scaffold for a different platform:

.. code-block:: console

    $ briefcase create <platform>

To create a scaffold for a specific output format:

.. code-block:: console

    $ briefcase create <platform> <output format>

If a scaffold for the nominated platform already exists, you'll be prompted
to delete and regenerate the app.

Options
=======

There are no additional command line options.
