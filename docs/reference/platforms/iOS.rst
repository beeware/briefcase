===
iOS
===

When generating an iOS project, Briefcase produces an Xcode project.

Icon format
===========

iOS projects use ``.png`` format icons. An application must provide icons of
the following sizes:

  * 20px
  * 29px
  * 40px
  * 58px
  * 60px
  * 76px
  * 80px
  * 87px
  * 120px
  * 152px
  * 167px
  * 180px
  * 1024px

Splash Image format
===================

iOS projects use ``.png`` format splash screen images. A splash screen should
be a square, transparent image, provided in the following sizes:

  * 1024px
  * 2048px
  * 3072px

You can specify a background color for the splash screen using the
``splash_background_color`` configuration setting.

iOS projects do not support installer images.

Additional options
==================

The following options can be provided at the command line when producing
iOS projects

build
-----

``-d <device>`` / ``--device <device>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The device simulator to target. Can be either a UDID, a device name (e.g.,
``"iPhone 11"``), or a device name and OS version (``"iPhone 11::13.3"``).

run
---

``-d <device>`` / ``--device <device>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The device simulator to target. Can be either a UDID, a device name (e.g.,
``"iPhone 11"``), or a device name and OS version (``"iPhone 11::13.3"``).
