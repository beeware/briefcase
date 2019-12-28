=========
macOS DMG
=========

A macOS DMG (Disk iMaGe) is a common format for distributing macOS content.
It presents itself to the operating system a disk that can be mounted; the
image then contains the files being distributed. For this reason, DMGs are
often used for distributing new applications, especially when there

Briefcase's DMG support is an extension of ``.app`` bundle support. The DMG
created by Briefcase contains a ``.app`` bundle for the application, plus a
symbolic link to the user's ``/Applications`` folder; this enables the user to
install their application by mounting the DMG, and dragging the application's
icon onto the icon for the ``/Applications`` folder contained in the DMG.
A background image can be provided to provide an additional visual hint for
the installation action.

Icon format
===========

macOS DMGs use ``.icns`` format icons for the application and installer.

Image format
============

macOS DMGs do not support splash screens. The installer background must be
in ``.png`` format.

Additional options
==================

The following options can be provided at the command line when producing
DMGs.

publish
-------

``--no-sign``
~~~~~~~~~~~~~

Don't perform code signing on the ``.app`` bundles in the DMG.

``-i <identity>`` / ``--identity <identity>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The code signing identity to use when signing the ``.app`` bundles in the DMG.
