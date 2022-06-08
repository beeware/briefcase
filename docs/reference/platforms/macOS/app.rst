===========
.app bundle
===========

A macOS ``.app`` bundle is a collection of directory with a specific layout,
and with some key metadata. If this structure and metadata exists, macOS treats
the folder as an executable file, giving it an icon.

``.app`` bundles can be copied around as if they are a single file. They can
also be compressed to reduce their size for transport.

By default, apps will be both signed and notarized when they are packaged.

The ``.app`` bundle is a distributable artefact. Alternatively, the ``.app``
bundle can be packaged as a ``.dmg`` that contains the ``.app`` bundle. The
default packaging format is ``.dmg``.

Icon format
===========

macOS ``.app`` bundles use ``.icns`` format icons.

Splash Image format
===================

macOS ``.app`` bundles do not support splash screens or installer images.

Additional options
==================

The following options can be provided at the command line when packaging
macOS apps.

``--no-notarize``
~~~~~~~~~~~~~~~~~

Do not submit the application for notarization. By default, apps will be
submitted for notarization unless they have been signed with an ad-hoc
signing identity.
