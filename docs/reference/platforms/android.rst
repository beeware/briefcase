=======
Android
=======

When generating an Android project, Briefcase produces a Gradle project.

Icon format
===========

Android projects use ``.png`` format icons, in round and square variants. An
application must provide the icons in the following sizes, for 2 variants:

  * ``round``:

    * 48px
    * 72px
    * 96px
    * 144px
    * 192px

  * ``square``:

    * 48px
    * 72px
    * 96px
    * 144px
    * 192px

Splash Image format
===================

Android projects use ``.png`` format splash screen images. A splash screen
should be a square image with a transparent background. It must be specified
in a range of sizes and variants, to suit different possible device sizes
and device display densities:

  * ``normal`` (typical phones; up to 480 density-independent pixels):

    * 320px
    * 480px (hdpi)
    * 640px (xhdpi)
    * 1280px (xxxhdpi)

  * ``large`` (large format phones, or phone-tablet "phablet" hybrids; up to
    720 density-indpendent pixels):

    * 480px
    * 720px (hdpi)
    * 960px (xhdpi)
    * 1920px (xxxhdpi)

  * ``xlarge`` (tablets; larger than 720 density-independent pixels)

    * 720px
    * 1080px (hdpi)
    * 1440px (xhdpi)
    * 2880px (xxxhdpi)

Consult `the Android documentation
<https://developer.android.com/training/multiscreen/screensizes>`__
for more details on devices, sizes, and display densities. `This list of common
devices with their sizes and DPI <https://material.io/resources/devices/>`__
may also be helpful.

You can specify a background color for the splash screen using the
``splash_background_color`` configuration setting.

Android projects do not support installer images.

Application configuration
=========================

The following options can be added to the
``tool.briefcase.app.<appname>.android`` section of your ``pyproject.toml``
file.

``version_code``
----------------

In addition to a version number, Android projects require a version "code".
This code is an integer version of your version number that *must* increase
with every new release pushed to the Play Store.

Briefcase will attempt to generate a version code by combining the version
number with the build number. It does this by using each part of the main
version number (padded to 3 digits if necessary) and the build number as 2
significant digits of the final version code:

  * Version ``1.0``, build 1 becomes ``1000001`` (i.e, `1`, `00`, `00`, `01`)
  * Version ``1.2``, build 37 becomes ``1020037`` (i.e., `1`, `02`, `00`, `37`)
  * Version ``1.2.37``, build 42 becomes ``1023742`` (i.e, `1`, `02`, `37`, `42`)
  * Version ``2020.6``, build 4 becomes ``2020060004`` (i.e., `2020`, `06`, `00`, `04`)

If you want to manually specify a version code by defining ``version_code`` in
your application configuration. If provided, this value will override any
auto-generated value.

Additional options
==================

The following options can be provided at the command line when producing
Android projects

build
-----

``-d <device>`` / ``--device <device>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The device simulator to target. Can be either a device ID, or a device name.

run
---

The device simulator to target. Can be either a device ID, or a device name.
