===============
Release History
===============

.. towncrier release notes start

0.3.11 (2022-10-14)
===================

Features
--------

* Added support for deploying an app as a static web page using PyScript. (#3)
* Briefcase log files are now stored in the ``logs`` subdirectory and only when the current directory is a Briefcase project. (#883)

Bugfixes
--------

* Output from spawned Python processes, such as when running ``briefcase dev``, is no longer buffered and displays in the console immediately. (#891)

Misc
----

* #848, #885, #887, #888, #889, #893, #894, #895, #896, #897, #899, #900, #908, #909, #910, #915


0.3.10 (2022-09-28)
===================

Features
--------

* iOS and Android now supports the installation of binary packages. (#471)
* Apps can now selectively remove files from the final app bundle using the ``cleanup_paths`` attribute. (#550)
* The Docker image for AppImage builds is created or updated for all commands instead of just ``create``. (#796)
* The performance of Briefcase's tool verification process has been improved. (#801)
* Briefcase templates are now versioned by the Briefcase version, rather than the Python version. (#824)
* Android commands now start faster, as they only gather a list of SDK packages when needed to write a log file. (#832)
* Log messages can be captured on iOS if they originate from a dynamically loaded module. (#842)
* Added an "open" command that can be used to open projects in IDEs. (#846)

Bugfixes
--------

* The Wait Bar is disabled for batch scripts on Windows to prevent hiding user prompts when CTRL+C is pressed. (#811)
* Android emulators that don't provide a model identifier can now be used to launch apps. (#820)
* All ``linuxdeploy`` plugins are made executable and ELF headers for AppImage plugins are patched for use in ``Docker``. (#829)
* The RCEdit plugin can now be upgraded. (#837)
* When verifying the existence of the Android emulator, Briefcase now looks for the actual binary, not the folder
  that contains the binary. This was causing false positives on some Android SDK setups. (#841)
* When CTRL+C is entered while an external program is running, ``briefcase`` will properly abort and exit. (#851)
* An issue with running `briefcase dev` on projects that put their application module in the project root has been resolved. (#863)

Improved Documentation
----------------------

* Added FAQ entries on the state of binary package support on mobile. (#471)

Misc
----

* #831, #834, #840, #844, #857, #859, #867, #868, #874, #878, #879


0.3.9 (2022-08-17)
==================

Features
--------

* Linux apps can now be packaged in Flatpak format. (#359)
* SDKs, tools, and other downloads needed to support app builds are now stored
  in an OS-native user cache directory instead of ``~/.briefcase``. (#374)
* Windows MSI installers can now be configured to ask the user whether they want
  a per-user or per-machine install. (#382)
* The console output of Windows apps is now captured and displayed during
  ``briefcase run``. (#620)
* Windows apps are now packaged with a stub application. This ensures that
  Windows apps present with the name and icon of the app, rather than the
  ``pythonw.exe`` name and icon. It also allows for improvements in logging and
  error handling. (#629)
* Temporary docker containers are now cleaned up after use. The wording of
  Docker progress messages has also been improved. (#774)
* Users can now define a ``BRIEFCASE_HOME`` environment variable. This allows
  you to specify the location of the Briefcase tool cache, allowing the user to
  avoid issues with spaces in paths or disk space limitations. (#789)
* Android emulator output is now printed to the console if it fails to start
  properly. (#799)
* ``briefcase android run`` now shows logs from only the current process, and
  includes all log tags except some particularly noisy and useless ones. It also
  no longer clears the Logcat buffer. (#814)


Bugfixes
--------

* Apps now have better isolation against the current working directory. This
  ensures that code in the current working directory isn't inadvertently
  included when an app runs. (#662)
* Windows MSI installers now install in ``Program Files``, rather than ``Program
  Files (x86)``. (#688)
* Linuxdeploy plugiuns can now be used when building Linux AppImages; this
  resolves many issues with GTK app deployment. (#756)
* Collision protection has been added to custom support packages that have the
  same name, but are served by different URLs. (#797)
* Python 3.7 and 3.8 on Windows will no longer deadlock when CTRL+C is sent
  during a subprocess command. (#809)


Misc
----

* #778, #783, #784, #785, #786, #787, #794, #800, #805, #810, #813, #815


0.3.8 (2022-06-27)
==================

Features
--------

* macOS apps are now notarized as part of the packaging process. (#365)
* Console output now uses Rich to provide visual highlights and progress bars. (#740)
* The macOS log streamer now automatically exits using the run command when the app exits. (#742)
* A verbose log is written to file when a critical error occurs or --log is specified. (#760)

Bugfixes
--------

* Updating an Android app now forces a re-install of the app. This corrects a problem (usually seen on physical devices) where app updates wouldn't be deployed if the app was already on the device. (#395)
* The iOS simulator is now able to correctly detect the iOS version when only a device name is provided. (#528)
* Windows MSI projects are now able to support files with non-ASCII filenames. (#749)
* The existence of an appropriate Android system image is now verified independently to the existence of the emulator. (#762)
* The error message presented when the Xcode Commandline Tools are installed, but Xcode is not, has been clarified. (#763)
* The METADATA file generated by Briefcase is now UTF-8 encoded, so it can handle non-Latin-1 characters. (#767)
* Output from subprocesses is correctly encoded, avoiding errors (especially on Windows) when tool output includes non-ASCII content. (#770)


Improved Documentation
----------------------

* Documented a workaround for ELF load command address/offset errors seen when using manylinux wheels. (#718)

Misc
----

* #743, #744, #755


0.3.7 (2022-05-17)
==================

Features
--------

* Apps can be updated as part of a call to package. (#473)
* The Android emulator can now be used on Apple M1 hardware. (#616)
* Names that are reserved words in Python (or other common programming languages) are now prevented when creating apps. (#617)
* Names that are invalid on Windows as filenames (such as CON and LPT0) are now invalid as app names. (#685)
* Verbose logging via -v and -vv now includes the return code, output, and environment variables for shell commands (#704)
* When the output of a wrapped command cannot be parsed, full command output, and failure reason is now logged. (#728)
* The iOS emulator will now run apps natively on M1 hardware, rather than through Rosetta emulation. (#739)


Bugfixes
--------

* Bundle identifiers are now validated to ensure they don't contain reserved words. (#460)
* The error reporting when the user is on an unsupported platform or Python version has been improved. (#541)
* When the formal name uses non-Latin characters, the suggested Class and App names are now valid. (#612)
* The code signing process for macOS apps has been made more robust. (#652)
* macOS app binaries are now adhoc signed by default, ensuring they can run on M1 hardware. (#664)
* Xcode version checks are now more robust. (#668)
* Android projects that have punctuation in their formal names can now build without error. (#696)
* Bundle name validation no longer excludes valid country identifiers (like ``in.example``). (#709)
* Application code and dist-info is now fully replaced during an update. (#720)
* Errors related to Java JDK detection now properly contain the value of JAVA_HOME instead of the word None (#727)
* All log entries will now be displayed for the run command on iOS and macOS; previously, initial log entries may have been omitted. (#731)
* Using CTRL+C to stop showing Android emulator logs while running the app will no longer cause the emulator to shutdown. (#733)


Misc
----

* #680, #681, #699, #726, #734


0.3.6 (2022-02-28)
==================

Features
--------

* On macOS, iOS, and Android, ``briefcase run`` now displays the application logs once the application has started. (#591)
* Xcode detection code now allows for Xcode to be installed in locations other than ``/Applications/Xcode.app``. (#622)
* Deprecated support for Python 3.6. (#653)


Bugfixes
--------

* Existing app packages are now cleared before reinstalling dependencies. (#644)
* Added binary patcher for linuxtools AppImage to increase compatibility. (#667)


Improved Documentation
----------------------

* Documentation on creating macOS/iOS code signing identities has been added (#641)


Misc
----

* #587, #588, #592, #598, #621, #643, #654, #670


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
