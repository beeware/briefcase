=============
Xcode project
=============

Briefcase supports creating a full Xcode project for a macOS app. This project
can then be used to build an actual app bundle, with the ``briefcase build``
command or directly from Xcode.

By default, apps will be both signed and notarized when they are packaged.

The Xcode project will produce a ``.app`` bundle is a distributable artefact.
Alternatively, this ``.app`` bundle can be packaged as a ``.dmg`` that contains
the ``.app`` bundle. The default packaging format is ``.dmg``.

Icon format
===========

macOS Xcode projects use ``.png`` format icons. An application must provide icons of
the following sizes:

  * 16px
  * 32px
  * 64px
  * 128px
  * 256px
  * 512px
  * 1024px

Splash Image format
===================

macOS Xcode projects do not support splash screens.

Additional options
==================

The following options can be provided at the command line when packaging
macOS apps.

``--no-notarize``
~~~~~~~~~~~~~~~~~

Do not submit the application for notarization. By default, apps will be
submitted for notarization unless they have been signed with an ad-hoc
signing identity.
