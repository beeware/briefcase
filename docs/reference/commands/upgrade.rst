=======
upgrade
=======

Briefcase uses external tools to manage the process of packaging apps. Where
possible, Briefcase will manage the process of obtaining those tools. This
is currently done for

 * **WiX** (used by the Windows MSI backend)
 * **linuxdeploy** (used by the Linux AppImage backend)
 * **Java JDK** (used by the Android backed)
 * **Android SDK** (used by the Android backend)

Over time, it may be necessary to upgrade these tools. The ``upgrade`` command
provides a way to perform these upgrades.

If you are managing your own version of these tools (e.g., if you have
downloaded a version of WiX and have set the ``WIX_HOME`` environment variable),
you must manage any upgrades on your own.

Usage
=====

To see what tools are currently being managed by Briefcase::

    $ briefcase upgrade --list

To upgrade all the tools that are currently being managed by Briefcase::

    $ briefcase upgrade

To upgrade a specific tool::

    $ briefcase upgrade <tool_name>

Options
=======

The following options can be provided at the command line.

``-l`` / ``--list``
-------------------

List the tools that are currently being managed by Briefcase.
