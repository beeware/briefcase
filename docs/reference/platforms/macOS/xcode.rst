=============
Xcode project
=============

Briefcase supports creating a full Xcode project for a macOS app. This project
can then be used to build an actual app bundle, with the ``briefcase build``
command or directly from Xcode.

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
