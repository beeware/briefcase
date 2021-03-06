===============
Release History
===============

.. towncrier release notes start

0.3.5 (2021-03-06)
==================

Features
--------

* macOS projects can now be generated as an Xcode project. (#523)

Bugfixes
--------

* macOS apps are now built as an embedded native binary, rather than a shell
  script invoking a Python script. This was necessary to provide better support
  for macOS app notarization and sandboxing. (#523)
* Fixed the registration of setuptools entry points caused by a change in case
  sensitivity handling in Setuptools 53.1.0. (#574)

Misc
----

* #562


0.3.4 (2021-01-03)
==================

Features
--------

* Added signing options for all platforms. App signing is only implemented on
  macOS, but ``--no-sign`` can now be used regardless of your target platform. (#486)
* Windows MSI installers can be configured to be per-machine, system-wide installers. (#498)
* Projects can specify a custom branch for the template used to generate the app. (#519)
* Added the `--no-run` flag to the *dev* command. This allows developers to
  install app dependencies without running the app. (#522)
* The new project wizard will now warn users when they select a platform that
  doesn't support mobile deployment. (#539)

Bugfixes
--------

* Modified the volume mounting process to allow for SELinux. (#500)
* Fixed missing signature for Python executable in macOS app bundle. This enables
  the packaged dmg to be notarized by Apple. (#514)
* Modified the Windows tests to allow them to pass on 32-bit machines. (#521)
* Fixed a crash when running with verbose output. (#532)

Improved Documentation
----------------------

* Clarified documentation around system_requires dependencies on Linux. (#459)

Misc
----

* #465, #475, #496, #512, #518


0.3.3 (2020-07-18)
==================

Features
--------

* WiX is now auto-downloaded when the MSI backend is used. (#389)
* The ``upgrade`` command now provides a way to upgrade tools that Briefcase has
  downloaded, including WiX, Java, linuxdeploy, and the Android SDK. (#450)

Bugfixes
--------

* Binary modules in Linux AppImages are now processed correctly, ensuring that no
  references to system libraries are retained in the AppImage. (#420)
* If pip is configured to use a per-user site_packages, this no longer clashes
  with the installation of application packages. (#441)
* Docker-using commands now check whether the Docker daemon is running and if
  the user has permission to access it. (#442)


0.3.2 (2020-07-04)
==================

Features
--------

* Added pytest coverage to CI/CD process. (#417)
* Application metadata now contains a ``Briefcase-Version`` indicator. (#425)
* The device list returned by ``briefcase run android`` now uses the Android
  device model name and unique ID e.g. a Pixel 3a shows up as ``Pixel 3a
  (adbDeviceId)``. (#433)
* Android apps are now packaged in Android App Bundle format. This allows the
  Play Store to dynmically build the smallest APK appropriate to a device
  installing an app. (#438)
* PursuedPyBear is now included in the new project wizard. (#440)

Bugfixes
--------

* iOS builds will now warn if the Xcode command line tools are the active.
  (#397)
* Linux Docker builds no longer use interactive mode, allowing builds to run on
  CI (or other TTY-less devices). (#439)

Improved Documentation
----------------------

* Documented the process of signing Android apps & publishing them to the Google
  Play store. (#342)

Misc
----

* #428


0.3.1 (2020-06-13)
==================

Features
--------

* The Linux AppImage backend has been modified to use Docker. This ensures that
  the AppImage is always built in an environment that is compatible with the
  support package. It also enables Linux AppImages to be built on macOS and
  Windows. "Native" builds (i.e., builds that *don't* use Docker) can be invoked
  using the ``--no-docker`` argument. (#344)
* A ``PYTHONPATH`` property has been added to ``AppConfig`` that describes the
  ``sys.path`` changes needed to run the app. (#401)
* Ad-hoc code signing is now possible on macOS with ``briefcase package
  --adhoc-sign``. (#409)
* Android apps can now use use ``-`` in their bundle name; we now convert ``-``
  to ``_`` in the resulting Android package identifier and Java package name. (#415)
* Mobile applications now support setting the background color of the splash
  screen, and setting a build identifier. (#422)
* Android now has a ``package`` command that produces the release APK. After
  manually signing this APK, it can be published to the Google Play Store. (#423)

Bugfixes
--------

* Some stray punctuation in the Android device helper output has been removed. (#396)
* An explicit version check for Docker is now performed. (#402)
* The Linux build process ensures the Docker user matches the UID/GID of the host
  user. (#403)
* Briefcase now ensures that the Python installation ecosystem tools (``pip``,
  ``setuptools``, and ``wheel``), are all present and up to date. (#421)

Improved Documentation
----------------------

* Documented that Windows MSI builds produce per-user installable MSI installers,
  while still supporting per-maching installs via the CLI. (#382)
* ``CONTRIBUTING.md`` has been updated to link to Briefcase-specific
  documentation. (#404)
* Removed references to the ``build-system`` table in ``pyproject.toml``. (#410)

Misc
----

* #380, #384


0.3.0 (2020-04-18)
==================
Features
--------

* Converted Briefcase to be a PEP518 tool, rather than a setuptools extension. (#266)


0.2.10
======

* Improved pre-detection of XCode and related tools
* Improved error handling when starting external tools
* Fixed iOS simulator integration

0.2.9
=====

* Updated mechanism for starting the iOS simulator
* Added support for environment markers in ``install_requires``
* Improved error handling when Wix isn't found

0.2.8
=====

* Corrects packaging problem with urllib3, caused by inconsistency between requests and boto3.
* Corrected problems with Start menu targets being created on Windows.

0.2.7
=====

* Added support for launch images for iPhone X, Xs, Xr, Xs Max and Xr Max
* Completed removal of internal pip API dependencies.

0.2.6
=====

* Added support for registering OS-level document type handlers.
* Removed dependency on an internal pip API.
* Corrected invocation of gradlew on Windows
* Addressed support for support builds greater than b9.

0.2.5
=====

 * Restored download progress bars when downloading support packages.

0.2.4
=====

 * Corrected a bug in the iOS backend that prevented iOS builds.

0.2.3
=====

 * Bugfix release, correcting the fix for pip 10 support.

0.2.2
=====

 * Added compatibility with pip 10.
 * Improved Windows packaging to allow for multiple executables
 * Added a ``--clean`` command line option to force a refresh of generated code.
 * Improved error handling for bad builds

0.2.1
=====

 * Improved error reporting when a support package isn't available.

0.2.0
=====

 * Added ``-s`` option to launch projects
 * Switch to using AWS S3 resources rather than Github Files.

0.1.9
=====

 * Added a full Windows installer backend

0.1.8
=====

 * Modified template rollout process to avoid API limits on Github.

0.1.7
=====

 * Added check for existing directories, with the option to replace
   existing content.
 * Added a Linux backend.
 * Added a Windows backend.
 * Added a splash screen for Android

0.1.6
=====

 * Added a Django backend (@glasnt)

0.1.5
=====

 * Added initial Android template
 * Force versions of pip (>= 8.1) and setuptools (>=27.0)
 * Drop support for Python 2

0.1.4
=====

 * Added support for tvOS projects
 * Moved to using branches in the project template repositories.

0.1.3
=====

 * Added support for Android projects using VOC.

0.1.2
=====

 * Added support for having multi-target support projects. This clears the way
   for Briefcase to be used for watchOS and tvOS projects, and potentially
   for Python-OSX-support and Python-iOS-support to be merged into a single
   Python-Apple-support.

0.1.1
=====

 * Added support for app icons and splash screens.

0.1.0
=====

Initial public release.
