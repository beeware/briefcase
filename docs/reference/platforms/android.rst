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
Android projects:

run
---

``-d <device>`` / ``--device <device>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The device or emulator to target. Can be specified as:

* ``@`` followed by an AVD name (e.g., ``@beePhone``); or
* a device ID (a hexadecimal identifier associated with a specific hardware device);
  or
* a JSON dictionary specifying the properties of a device that will be created.
  This dictionary must have, at a minimum, an AVD name::

     $ briefcase run -d '{"avd":"new-device"}'

  You may also specify:

  - ``device_type`` (e.g., ``pixel``) - the type of device to emulate
  - ``skin`` (e.g., ``pixel_3a``) - the skin to apply to the emulator
  - ``system_image`` (e.g., ``system-images;android-31;default;arm64-v8a``) - the Android
    system image to use in the emulator.

  If any of these attributes are *not* specified, they will fall back
  to reasonable defaults.

``--Xemulator=<value>``
~~~~~~~~~~~~~~~~~~~~~~~

A configuration argument to be passed to the emulator on startup. For example,
to start the emulator in "headless" mode (i.e., without a display window),
specify ``--Xemulator=-no-window``. See `the Android documentation
<https://developer.android.com/studio/run/emulator-commandline>`__ for details
on the full list of options that can be provided.

You may specify multiple ``--Xemulator`` arguments; each one specifies a
single argument to pass to the emulator, in the order they are specified.

``--shutdown-on-exit``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instruct Briefcase to shut down the emulator when the run finishes. This is
especially useful if you are running in headless mode, as the emulator will
continue to run in the background, but there will be no visual manifestation
that it is running. It may also be useful as a cleanup mechanism when running
in a CI configuration.

Application configuration
=========================

The following options can be added to the
``tool.briefcase.app.<appname>.android`` section of your ``pyproject.toml``
file:

``build_gradle_extra_content``
------------------------------

A string providing additional Gradle settings to use when building your app.
This will be added verbatim to the end of your ``app/build.gradle`` file.
