Release History
===============

0.2.5
-----

 * Restored download progress bars when downloading support packages.

0.2.4
-----

 * Corrected a bug in the iOS backend that prevented iOS builds.

0.2.3
-----

 * Bugfix release, correcting the fix for pip 10 support.

0.2.2
-----

 * Added compatibility with pip 10.
 * Improved Windows packaging to allow for multiple executables
 * Added a ``--clean`` command line option to force a refresh of generated code.
 * Improved error handling for bad builds

0.2.1
-----

 * Improved error reporting when a support package isn't available.

0.2.0
-----

 * Added ``-s`` option to launch projects
 * Switch to using AWS S3 resources rather than Github Files.

0.1.9
-----

 * Added a full Windows installer backend

0.1.8
-----

 * Modified template rollout process to avoid API limits on Github.

0.1.7
-----

 * Added check for existing directories, with the option to replace
   existing content.
 * Added a Linux backend.
 * Added a Windows backend.
 * Added a splash screen for Android

0.1.6
-----

 * Added a Django backend (@glasnt)

0.1.5
-----

 * Added initial Android template
 * Force versions of pip (>= 8.1) and setuptools (>=27.0)
 * Drop support for Python 2

0.1.4
-----

 * Added support for tvOS projects
 * Moved to using branches in the project template repositories.

0.1.3
-----

 * Added support for Android projects using VOC.

0.1.2
-----

 * Added support for having multi-target support projects. This clears the way
   for Briefcase to be used for watchOS and tvOS projects, and potentially
   for Python-OSX-support and Python-iOS-support to be merged into a single
   Python-Apple-support.

0.1.1
-----

 * Added support for app icons and splash screens.

0.1.0
-----

Initial public release.
