======
update
======

While you're developing an application, you may need to rapidly iterate on the
code, making small changes and then re-building. The update command applies
any changes you've made to your code to the packaged application code.

It will *not* update requirements or installer resources unless specifically
requested.

Usage
=====

To repackage your application's code for the current platform's default output
format:

.. code-block:: console

    $ briefcase update

To repackage your application's code for a different platform:

.. code-block:: console

    $ briefcase update <platform>

To repackage your application's code for a specific output format:

.. code-block:: console

    $ briefcase update <platform> <output format>

Options
=======

The following options can be provided at the command line.

``-a <app name>`` / ``--app <app name>``
----------------------------------------

Run a specific application target in your project. This argument is only
required if your project contains more than one application target. The app
name specified should be the machine-readable package name for the app.

``-r`` / ``--update-requirements``
----------------------------------

Update application requirements.

``--update-resources``
----------------------

Update application resources such as icons.

``--update-support``
--------------------

Update application support package.

``--update-stub``
-----------------

Update stub binary.
