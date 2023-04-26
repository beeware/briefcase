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

``-r`` / ``--update-requirements``
----------------------------------

Update application requirements.

``--update-resources``
----------------------

Update application resources (e.g., icons and splash screens).

``--update-support``
----------------------

Update application support package.
