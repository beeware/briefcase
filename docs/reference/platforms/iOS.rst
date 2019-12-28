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

Image format
============

iOS projects use ``.png`` format splash screen iamges. An application must
provide splash images of the following sizes:

  * 640x1136px
  * 640x960px
  * 750x1334px
  * 768x1004px
  * 768x1024px
  * 828x1792px
  * 1024x748px
  * 1024x768px
  * 1125x2436px
  * 1242x2208px
  * 1242x2688px
  * 1536x2008px
  * 1536x2048px
  * 1792x828px
  * 2048x1496px
  * 2048x1536px
  * 2208x1242px
  * 2436x1125px
  * 2688x1242px

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

The device simulator to target. Can be either a UDID, a device name (e.g.,
``"iPhone 11"``), or a device name and OS version (``"iPhone 11::13.3"``).
