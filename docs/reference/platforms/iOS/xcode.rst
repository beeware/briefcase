=================
iOS Xcode project
=================

+--------+-------+---------+--------+---+-----+--------+-----+-------+
| Host Platform Support (:ref:`platform-support-key`)                |
+--------+-------+---------+--------+---+-----+--------+-----+-------+
| macOS          | Windows              | Linux                      |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+
| x86‑64 | arm64 | x86 | x86‑64 | arm64 | x86 | x86‑64 | arm | arm64 |
+========+=======+=====+========+=======+=====+========+=====+=======+
| |f|    | |f|   |     |        |       |     |        |     |       |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+

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
* 640px
* 1024px
* 1280px
* 1920px

The icon will also be used to populate the splash screen. You can specify a
background color for the splash screen using the ``splash_background_color``
configuration setting.

iOS projects do not support installer images.

Colors
======

iOS allows for some customization of the colors used by your app:

* ``splash_background_color`` is the color of the splash background that
  displays while an app is loading.

Additional options
==================

The following options can be provided at the command line when producing
iOS projects:

run
---

``-d <device>`` / ``--device <device>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The device simulator to target. Can be either a UDID, a device name (e.g.,
``"iPhone 11"``), or a device name and OS version (``"iPhone 11::iOS 13.3"``).

Application configuration
=========================

The following options can be added to the ``tool.briefcase.app.<appname>.iOS.app``
section of your ``pyproject.toml`` file.

``info``
--------

A property whose sub-attributes define keys that will be added to the app's
``Info.plist`` file. Each entry will be converted into a key in the entitlements
file. For example, specifying::

    info."UIFileSharingEnabled" = true

will result in an ``Info.plist`` declaration of::

    <key>UIFileSharingEnabled</key><true/>

Any Boolean or string value can be used for an ``Info.plist`` value.

Permissions
===========

Briefcase cross platform permissions map to the following ``info`` keys:

* ``camera``: ``NSCameraUsageDescription``
* ``microphone``: ``NSMicrophoneUsageDescription``
* ``coarse_location``
  - ``NSLocationDefaultAccuracyReduced=True``
  - ``NSLocationWhenInUseUsageDescription`` if ``fine_location`` is not defined
* ``fine_location``
  - ``NSLocationDefaultAccuracyReduced=False``
  - ``NSLocationWhenInUseUsageDescription``
* ``background_location``:
  - ``NSLocationAlwaysAndWhenInUseUsageDescription``
  - ``NSLocationWhenInUseUsageDescription`` if neither ``fine_location`` or ``coarse_location`` is set
  - ``UIBackgroundModes`` will include ``location`` and ``processing``
* ``photo_library``: ``NSPhotoLibraryAddUsageDescription``

Platform quirks
===============

.. _ios-third-party-packages:

Availability of third-party packages
------------------------------------

Briefcase is able to use third-party packages in iOS apps. As long as the package is
available on PyPI, or you can provide a wheel file for the package, it can be added to
the ``requires`` declaration in your ``pyproject.toml`` file and used by your app at
runtime.

If the package is pure Python (i.e., it does not contain a binary library), that's all
you need to do. To check whether a package is pure Python, look at the PyPI downloads
page for the project; if the wheels provided are have a ``-py3-none-any.whl`` suffix,
then they are pure Python wheels. If the wheels have version and platform-specific
extensions (e.g., ``-cp311-cp311-macosx_11_0_universal2.whl``), then the wheel contains
a binary component.

If the package contains a binary component, that wheel needs to be compiled for iOS.
PyPI does not currently support uploading iOS-compatible wheels, so you can't rely on
PyPI to provide those wheels. Briefcase uses a `secondary repository
<https://anaconda.org/beeware/repo>`__ to store pre-compiled iOS wheels.

This repository is maintained by the BeeWare project, and as a result, it does not have
binary wheels for *every* package that is available on PyPI, or even every *version* of
every package that is on PyPI. If you see the message::

    ERROR: Could not find a version that satisfies the requirement <package name> (from versions: none)
    ERROR: No matching distribution found for <package name>

then the package (or the version that you've specified) probably isn't supported yet.

It is *usually* possible to compile any binary package wheels for iOS, depending on the
requirements of the package itself. If the package has a dependency on other binary
libraries (e.g., something like ``libjpeg`` that isn't written in Python), those
libraries will need to be compiled for iOS as well. However, if the library requires
build tools that don't support iOS, such as a compiler that can't target iOS, or a
PEP517 build system that doesn't support cross-compilation, it may not be possible to
build an iOS wheel.

The BeeWare Project provides the `Mobile Forge
<https://github.com/beeware/mobile-forge>`__ project to assist with cross-compiling iOS
binary wheels. This repository contains recipes for building the packages that are
stored in the `secondary package repository <https://anaconda.org/beeware/repo>`__.
Contributions of new package recipes are welcome, and can be submitted as pull requests.
Or, if you have a particular package that you'd like us to support, please visit the
`issue tracker <https://github.com/beeware/mobile-forge/issues>`__ and provide details
about that package.

Requirements cannot be provided as source tarballs
--------------------------------------------------

Briefcase *cannot* install packages published as source tarballs into an iOS app, even
if the package is a pure Python package that would produce a ``py3-none-any`` wheel.
This is an inherent limitation in the use of source tarballs as a distribution format.

If you need to install a package in an iOS app that is only published as a source
tarball, you'll need to compile that package into a wheel first. If the package is pure
Python, you can generate a ``py3-none-any`` wheel using ``pip wheel <package name>``. If
the project has a binary component, you'll need to use `Mobile Forge
<https://github.com/beeware/mobile-forge>`__ (or similar tooling) to compile compatible
wheels.

You can then directly add the wheel file to the ``requires`` definition for your app, or
put the wheel in a folder and add:

.. code-block:: TOML

    requirement_installer_args = ["--find-links", "<path-to-wheel-folder>"]

to your ``pyproject.toml``. This will instruct Briefcase to search that folder for
compatible wheels during the installation process.
