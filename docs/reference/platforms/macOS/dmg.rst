==========
macOS DMGs
==========

A macOS DMG (Disk iMaGe) is a common format for distributing macOS content.
It presents itself to the operating system a disk that can be mounted; the
image then contains the files being distributed. For this reason, DMGs are
often used for distributing new applications, especially

Briefcase's DMG support is an extension of the .app bundle support. The DMG
created by Briefcase contains a .app file for the application, plus a symbolic
link to the user's ``/Applications`` folder; this enables the user to install
their application by mounting the DMG, and dragging the application's icon
onto the icon for the ``/Applications`` folder contained in the DMG.

Creating a .app bundle
======================

To create a DMG, run::

    $ briefcase create macOS dmg

Options
=======

The following options can be used in ``pyproject.toml`` to configure an
application's DMG.

``icon``
--------

An icon for the application, in ``.icns`` format.

``installer_icon``
------------------

An icon for the mounted DMG.

``installer_background``
------------------------

An image to use as the background of the mounted DMG folder. Must be in PNG
format.
