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

* :attr:`splash_background_color` is the color of the splash background that
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

.. currentmodule:: iOS

The following options can be added to the ``tool.briefcase.app.<appname>.iOS.app``
section of your ``pyproject.toml`` file.

.. attribute:: info

A property whose sub-attributes define keys that will be added to the app's
``Info.plist`` file. Each entry will be converted into a key in the entitlements
file. For example, specifying::

    info."UIFileSharingEnabled" = true

will result in an ``Info.plist`` declaration of::

    <key>UIFileSharingEnabled</key><true/>

Any Boolean or string value can be used for an ``Info.plist`` value.

.. attribute:: min_os_version

The minimum iOS version that the app will support. This controls the value of
``IPHONEOS_DEPLOYMENT_TARGET`` used when building the app.

Permissions
===========

Briefcase cross platform permissions map to the following :attr:`info` keys:

* :attr:`permission.camera`: ``NSCameraUsageDescription``
* :attr:`permission.microphone`: ``NSMicrophoneUsageDescription``
* :attr:`permission.coarse_location`:

  - ``NSLocationDefaultAccuracyReduced=True``
  - ``NSLocationWhenInUseUsageDescription`` if ``fine_location`` is not defined

* :attr:`permission.fine_location`:

  - ``NSLocationDefaultAccuracyReduced=False``
  - ``NSLocationWhenInUseUsageDescription``

* :attr:`permission.background_location`:

  - ``NSLocationAlwaysAndWhenInUseUsageDescription``
  - ``NSLocationWhenInUseUsageDescription`` if neither
    :attr:`permission.fine_location` or
    :attr:`permission.coarse_location` is set
  - ``UIBackgroundModes`` will include ``location`` and ``processing``

* :attr:`permission.photo_library`: ``NSPhotoLibraryAddUsageDescription``

Platform quirks
===============

.. _ios-third-party-packages:

Availability of third-party packages
------------------------------------

Briefcase is able to use third-party packages in iOS apps. As long as the package is
available on PyPI, or you can provide a wheel file for the package, it can be added to
the :attr:`requires` declaration in your ``pyproject.toml`` file and used by your app at
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

You can then directly add the wheel file to the :attr:`requires` definition for your app, or
put the wheel in a folder and add:

.. code-block:: TOML

    requirement_installer_args = ["--find-links", "<path-to-wheel-folder>"]

to your ``pyproject.toml``. This will instruct Briefcase to search that folder for
compatible wheels during the installation process.

Executable binary content in wheels
-----------------------------------

The iOS App Store has very stringent constraints on what can be included in an app
bundle, and where it can be included. One of those constraints is that any executable
content must be distributed as a framework, in the ``Frameworks`` folder of the iOS
project.

Briefcase's app template will process binary wheels to satisfy this requirement.
However, it will only process binary content that is executable at runtime. Some
packages (NumPy is one notable example) are known to distribute additional executable
files, such as statically linked ``.a`` libraries, in their wheel content. These files
are not usable at runtime, and Briefcase will not process them. If they're present in an
app bundle at time of submission to the App Store, your app will not pass app
validation, raising errors like:

    Error: Validation failed Invalid bundle structure. The ``.../libsomething.a`` binary
    file is not permitted. Your app cannot contain standalone executables or libraries,
    other than a valid CFBundleExecutable of supported bundles.

To avoid this, you must purge any binary content from your app before submission. You
can do this using the ``cleanup_paths`` configuration option::

    cleanup_paths = [
        "*/app_packages.*/**/*.a",
    ]

This will find and purge all ``.a`` content in your app's dependencies. You can add
additional patterns to remove other problematic content.


Deployment to Simulated and Physical iOS Devices
------------------------------------------------

Briefcase provides support for deployment to simulated iOS devices through the
command line.

If you want to deploy to a physical iOS device, you will need need to use Xcode through
the following steps:

1. Run ``briefcase open ios`` in the command line. This will open your application in Xcode.
2. Setup your Apple Developer account with your certificate in Xcode.
3. In the project navigator, select your application at the top level (the root of the project).
4. Select the `Signing and Capabilities` tab in the editor area.
5. Select your Apple Developer team or individual account from the `Team` drop-down.
6. Select your specific device.
7. Press the run button.
