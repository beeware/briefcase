==============
Gradle project
==============

+--------+-------+---------+--------+---+-----+--------+-----+-------+
| Host Platform Support (:ref:`platform-support-key`)                |
+--------+-------+---------+--------+---+-----+--------+-----+-------+
| macOS          | Windows              | Linux                      |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+
| x86‑64 | arm64 | x86 | x86‑64 | arm64 | x86 | x86‑64 | arm | arm64 |
+========+=======+=====+========+=======+=====+========+=====+=======+
| |f|    | |y|   |     | |f|    |       | |v| | |f|    | |v| | |v|   |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+

When generating an Android project, Briefcase produces a Gradle project.

Environment
===========

Gradle requires an install of a Java 17 JDK and the Android SDK.

If the methods below fail to find an Android SDK or Java JDK, Briefcase will
download and install an isolated copy in its data directory.

Java JDK
--------

If you have an existing install of a Java 17 JDK, it will be used by Briefcase
if the ``JAVA_HOME`` environment variable is set. On macOS, if ``JAVA_HOME`` is
not set, Briefcase will use the ``/usr/libexec/java_home`` tool to find an
existing JDK install.

Android SDK
-----------

If you have an existing install of the Android SDK, it will be used by Briefcase
if the ``ANDROID_HOME`` environment variable is set. If ``ANDROID_HOME`` is not
present in the environment, Briefcase will honor the deprecated
``ANDROID_SDK_ROOT`` environment variable. Additionally, an existing SDK install
must have version 19.0 of Command-line Tools installed; this version can be
installed in the SDK Manager in Android Studio.

Packaging format
================

Briefcase supports three packaging formats for an Android app:

1. An AAB bundle (the default output of ``briefcase package android``, or by using
   ``briefcase package android -p aab``); or
2. A Release APK (by using ``briefcase package android -p apk``); or
3. A Debug APK (by using ``briefcase package android -p debug-apk``).

Icon format
===========

Android projects use ``.png`` format icons, in round, square and adaptive variants. An
application must provide the icons in the following sizes, for 3 variants:

* ``round``:

  * 48px (``mdpi``; baseline resolution)
  * 72px (``hdpi``; 1.5x scale)
  * 96px (``xhdpi``; 2x scale)
  * 144px (``xxhdpi``; 3x scale)
  * 192px (``xxxhdpi``; 4x scale)

* ``square``:

  * 48px (``mdpi``; baseline resolution)
  * 72px (``hdpi``; 1.5x scale)
  * 96px (``xhdpi``; 2x scale)
  * 144px (``xxhdpi``; 3x scale)
  * 192px (``xxxhdpi``; 4x scale)
  * 320px (``mdpi``; baseline resolution for splash screen)
  * 480px (``hdpi``; 1.5x scale for splash screen)
  * 640px (``xhdpi``; 2x scale for splash screen)
  * 960px (``xxhdpi``; 3x scale for splash screen)
  * 1280px (``xxxhdpi``; 4x scale for splash screen)

* ``adaptive``:

  * 108px (``mdpi``; baseline resolution; 66px drawable area)
  * 162px (``hdpi``; 1.5x scale; 99px drawable area)
  * 216px (``xhdpi``; 2x scale; 132px drawable area)
  * 324px (``xxhdpi``; 3x scale; 198px drawable area)
  * 432px (``xxxhdpi``; 4x scale; 264px drawable area)

The ``round`` and ``square`` icons should include their background color in the image.
The ``adaptive`` icons should have a transparent background; the icon image should be
centered in the overall image, and should not exceed the drawable area. The background
color of the adaptive icon will be the value specified with ``splash_background_color``.

The icon will also be used to populate the splash screen. You can specify a
background color for the splash screen using the ``splash_background_color``
configuration setting.

Android projects do not support installer images.

Colors
======

Android allows for some customization of the colors used by your app:

* ``base_theme`` is used to set the base Android theme.
* ``accent_color`` is used as a subtle highlight throughout your app to
  call attention to key elements. It's used on things like form labels and
  inputs.
* ``primary_color`` is the main branding color of the app and is used to
  color the app bar in the main window.
* ``primary_color_dark`` is used alongside the primary color to color the
  status bar at the top of the screen.
* ``splash_background_color`` is the color of the splash background that
  displays while an app is loading.

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
  This dictionary must have, at a minimum, an AVD name:

  .. code-block:: console

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

The following options can be added to the ``tool.briefcase.app.<appname>.android``
section of your ``pyproject.toml`` file.

``android_manifest_attrs_extra_content``
----------------------------------------

Additional attributes that will be added verbatim to the ``<manifest>`` declaration of
the ``AndroidManifest.xml`` of your app.

``android_manifest_extra_content``
----------------------------------

Additional content that will be added verbatim just before the closing ``</manifest>``
declaration of the ``AndroidManifest.xml`` of your app.

``android_manifest_application_attrs_extra_content``
----------------------------------------------------

Additional attributes that will be added verbatim to the ``<application>`` declaration
of the ``AndroidManifest.xml`` of your app.

``android_manifest_application_extra_content``
----------------------------------------------

Additional content that will be added verbatim just before the closing
``</application>`` declaration of the ``AndroidManifest.xml`` of your app.

``android_manifest_activity_attrs_extra_content``
-------------------------------------------------

Additional attributes that will be added verbatim to the ``<activity>`` declaration of
the ``AndroidManifest.xml`` of your app.

``android_manifest_activity_extra_content``
-------------------------------------------

Additional content that will be added verbatim just before the closing ``</activity>``
declaration of the ``AndroidManifest.xml`` of your app.

``base_theme``
--------------

The base theme for the application. Defaults to ``Theme.AppCompat.Light.DarkActionBar``

``build_gradle_dependencies``
-----------------------------

The list of libraries that should be linked into the Android application. Each library
should be a versioned Maven package specifier. If unspecified, three libraries will be
linked into the app:

* ``androidx.appcompat:appcompat:1.0.2``
* ``androidx.constraintlayout:constraintlayout:1.1.3``
* ``androidx.swiperefreshlayout:swiperefreshlayout:1.1.0``

``build_gradle_extra_content``
------------------------------

A string providing additional Gradle settings to use when building your app.
This will be added verbatim to the end of your ``app/build.gradle`` file.

``feature``
-----------

A property whose sub-properties define the features that will be marked as required by
the final app. Each entry will be converted into a ``<uses-feature>`` declaration in
your app's ``AndroidManifest.xml``, with the feature name matching the name of the
sub-attribute.

For example, specifying::

    feature."android.hardware.bluetooth" = true

will result in an ``AndroidManifest.xml`` declaration of::

    <uses-feature android:name="android.hardware.bluetooth" android:required="true">

The use of some cross-platform permissions will imply the addition of features; see
:ref:`the discussion on Android permissions <android-permissions>` for more details.

``min_os_version``
------------------

The minimum API level that the app will support (i.e., the ``minSdkVersion`` for the
app). This is *not* the Android version; it is the underlying API level. For example,
Android 9 uses an API level of 28; if you wanted to specify Android 9 as your minimum
supported version, you would define ``min_os_version = "28"``.

``permission``
--------------

A property whose sub-properties define the platform-specific permissions that will be
marked as required by the final app. Each entry will be converted into a
``<uses-permission>`` declaration in your app's ``AndroidManifest.xml``, with the
feature name matching the name of the sub-attribute.

For example, specifying::

    permission."android.permission.HIGH_SAMPLING_RATE_SENSORS" = true

will result in an ``AndroidManifest.xml`` declaration of::

    <uses-permission android:name="android.permission.HIGH_SAMPLING_RATE_SENSORS">

``target_os_version``
----------------------

The API level that the app will target. This controls the version of the Android SDK that
is used to build your app (by setting the ``compileSdkVersion`` for your app), and the
forwards compatibility behavioral changes your app will enable (by setting the
``targetSdkVersion`` setting). This is *not* the Android version; it is the underlying
API level. For example, Android 15 uses an API level of 35; if you wanted to specify
Android 15 as your target API level, you would define ``target_os_version = "35"``.

``version_code``
----------------

In addition to a version number, Android projects require a version "code".
This code is an integer version of your version number that *must* increase
with every new release pushed to the Play Store.

Briefcase will attempt to generate a version code by combining the version
number with the build number. It does this by using each part of the main
version number (padded to 3 digits if necessary) and the build number as 2
significant digits of the final version code:

  * Version ``1.0``, build 1 becomes ``1000001`` (i.e, ``1``, ``00``, ``00``, ``01``)
  * Version ``1.2``, build 37 becomes ``1020037`` (i.e., ``1``, ``02``, ``00``, ``37``)
  * Version ``1.2.37``, build 42 becomes ``1023742`` (i.e, ``1``, ``02``, ``37``, ``42``)
  * Version ``2020.6``, build 4 becomes ``2020060004`` (i.e., ``2020``, ``06``, ``00``, ``04``)

If you want to manually specify a version code by defining ``version_code`` in
your application configuration. If provided, this value will override any
auto-generated value.

.. _android-permissions:

Permissions
===========

Briefcase cross platform permissions map to ``<uses-permission>`` declarations in the
app's ``AppManifest.xml``:

* ``camera``: ``android.permission.CAMERA``
* ``microphone``: ``android.permission.RECORD_AUDIO``
* ``coarse_location``: ``android.permission.ACCESS_COARSE_LOCATION``
* ``fine_location``: ``android.permission.ACCESS_FINE_LOCATION``
* ``background_location``: ``android.permission.ACCESS_BACKGROUND_LOCATION``
* ``photo_library``: ``android.permission.READ_MEDIA_VISUAL_USER_SELECTED``

Every application will be automatically granted the ``android.permission.INTERNET`` and
``android.permission.NETWORK_STATE`` permissions.

Specifying a ``camera`` permission will result in the following non-required ``feature``
definitions being implicitly added to your app:

* ``android.hardware.camera``,
* ``android.hardware.camera.any``,
* ``android.hardware.camera.front``,
* ``android.hardware.camera.external`` and
* ``android.hardware.camera.autofocus``.

Specifying the ``coarse_location``, ``fine_location`` or ``background_location``
permissions will result in the following non-required ``feature`` declarations being
implicitly added to your app:

* ``android.hardware.location.network``
* ``android.hardware.location.gps``

This is done to ensure that an app is not prevented from installing if the device
doesn't have the given features. You can make the feature explicitly required by
manually defining these feature requirements. For example, to make GPS hardware
required, you could add the following to the Android section of your
``pyproject.toml``::

    feature."android.hardware.location.gps" = True

Platform quirks
===============

.. _android-third-party-packages:

Availability of third-party packages
------------------------------------

Briefcase is able to use third-party packages in Android apps. As long as the package is
available on PyPI, or you can provide a wheel file for the package, it can be added to
the ``requires`` declaration in your ``pyproject.toml`` file and used by your app at
runtime.

If the package is pure Python (i.e., it does not contain a binary library), that's all
you need to do. To check whether a package is pure Python, look at the PyPI downloads
page for the project; if the wheels provided are have a ``-py3-none-any.whl`` suffix,
then they are pure Python wheels. If the wheels have version and platform-specific
extensions (e.g., ``-cp311-cp311-macosx_11_0_universal2.whl``), then the wheel contains
a binary component.

If the package contains a binary component, that wheel needs to be compiled for Android.
PyPI does not currently support uploading Android-compatible wheels, so you can't rely
on PyPI to provide those wheels. Briefcase uses a `secondary repository
<https://chaquo.com/pypi-13.1/>`__ to provide pre-compiled Android wheels.

This repository is maintained by the BeeWare project, and as a result, it does not have
binary wheels for *every* package that is available on PyPI, or even every *version* of
every package that is on PyPI. If you see any of the following messages when building an
app for a mobile platform, then the package (or this version of it) probably isn't
supported yet:

* The error `"Chaquopy cannot compile native code"
  <https://chaquo.com/chaquopy/doc/current/faq.html#chaquopy-cannot-compile-native-code>`__
* A reference to downloading a ``.tar.gz`` version of the package
* A reference to ``Building wheels for collected packages: <package>``

It is *usually* possible to compile any binary package wheels for Android, depending on
the requirements of the package itself. If the package has a dependency on other binary
libraries (e.g., something like ``libjpeg`` that isn't written in Python), those
libraries will need to be compiled for Android as well. However, if the library requires
build tools that don't support Android, such as a compiler that can't target Android, or
a PEP517 build system that doesn't support cross-compilation, it may not be possible to
build an Android wheel.

The `Chaquopy repository <https://github.com/chaquo/chaquopy/blob/master/server/pypi/README.md>`__
contains tools to assist with cross-compiling Android binary wheels. This repository contains
recipes for building the packages that are stored in the `secondary package repository
<https://chaquo.com/pypi-13.1/>`__. Contributions of new package recipes are welcome, and
can be submitted as pull requests. Or, if you have a particular package that you'd like
us to support, please visit the `issue tracker
<https://github.com/chaquo/chaquopy/issues>`__ and provide details about that package.

While it is possible to use `briefcase package android` to produce an APK or AAB
file for distribution, the file is *not* usable as-is. It must be signed
regardless of whether you're distributing your app through the Play Store, or
via loading the APK directly. For details on how to manually sign your code,
see the instructions on `signing an Android App Bundle
<https://briefcase.readthedocs.io/en/stable/how-to/publishing/android.html#sign-the-android-app-bundle>`__.```
