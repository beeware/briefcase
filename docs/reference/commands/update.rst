======
update
======

While you're developing an application, you may need to rapidly iterate on the
code, making small changes and then re-building. The update command applies
any changes you've made to your codebase to the packaged application code.

It will *not* update dependencies or installer resources unless specifically
requested.

Usage
=====

To repackage your application's code for the current platform's default output
format::

    $ briefcase update

To repackage your application's code for a different platform::

    $ briefcase update <platform>

To repackage your application's code for a specific output format::

    $ briefcase update <platform> <output format>

Options
=======

The following options can be provided at the command line.

``-d`` / ``--update-dependencies``
----------------------------------

Update application dependencies.

``-r`` / ``--update-resources``
-------------------------------

Update application resources (e.g., icons and splash screens).
