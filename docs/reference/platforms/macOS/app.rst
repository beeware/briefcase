============
.app bundles
============

A macOS ``.app`` bundle is a collection of directory with a specific layout,
and with some key metadata. If this structure and metadata exists, macOS treats
the folder as an executable file, giving it an icon.

``.app`` bundles can be copied around as if they are a single file. They can
also be compressed to reduce their size for transport.

Creating a .app bundle
======================

To create a .app bundle, run::

    $ briefcase create macOS app

Options
=======

The following options can be used in ``pyproject.toml`` to configure an
application's ``.app`` bundle.

``icon``
--------

An icon for the application, in ``.icns`` format.
