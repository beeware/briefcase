===============
Release History
===============

.. towncrier release notes start

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
