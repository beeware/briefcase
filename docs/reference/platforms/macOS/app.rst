===========
.app bundle
===========

A macOS ``.app`` bundle is a collection of directory with a specific layout,
and with some key metadata. If this structure and metadata exists, macOS treats
the folder as an executable file, giving it an icon.

``.app`` bundles can be copied around as if they are a single file. They can
also be compressed to reduce their size for transport.

Icon format
===========

``.app`` bundles use ``.icns`` format icons.

Image format
============

``.app`` bundles do not support splash screens or installer images.

Additional options
==================

The following options can be provided at the command line when producing
``.app`` bundles.

publish
-------

``--no-sign``
~~~~~~~~~~~~~

Don't perform code signing on the ``.app`` bundles.

``-i <identity>`` / ``--identity <identity>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The code signing identity to use when signing the ``.app`` bundles.
