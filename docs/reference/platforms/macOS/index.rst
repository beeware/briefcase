=====
macOS
=====

.. toctree::
   :hidden:

   app
   xcode

+--------+-------+---------+--------+---+-----+--------+-----+-------+
| Host Platform Support (:ref:`platform-support-key`)                |
+--------+-------+---------+--------+---+-----+--------+-----+-------+
| macOS          | Windows              | Linux                      |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+
| x86‑64 | arm64 | x86 | x86‑64 | arm64 | x86 | x86‑64 | arm | arm64 |
+========+=======+=====+========+=======+=====+========+=====+=======+
| |f|    | |f|   |     |        |       |     |        |     |       |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+

Briefcase supports two output formats for macOS apps:

* An :doc:`./app` with a pre-compiled binary; and
* An :doc:`./xcode` which can be used to build an app with a customized
  binary.

The default output format for macOS is an :doc:`./app`.

Both output formats support packaging as a macOS DMG, PKG or as a standalone signed app
bundle. By default, apps will be both signed and notarized when they are packaged.

Configuration options between the :doc:`./app` and :doc:`./xcode` formats are identical.

Packaging format
================

Briefcase supports three packaging formats for a macOS app:

1. A DMG that contains the ``.app`` bundle (using ``briefcase package macOS -p dmg``).
2. A zipped ``.app`` bundle (using ``briefcase package macOS -p zip``).
3. A ``.pkg`` installer (using ``briefcase package macOS -p pkg``).

``.pkg`` is the *required* format for console apps. ``.dmg`` is the
default format for GUI apps.

Icon format
===========

macOS apps use ``.icns`` format icons.

macOS apps do not support splash screens or installer images.

Additional options
==================

The following options can be provided at the command line when packaging
macOS apps.

``--installer-identity <identity>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This option is only used when creating a ``.pkg`` installer.

The :doc:`code signing identity </how-to/code-signing/macOS>` to use when signing the
installer package. This is a *different* signing identity to the one used to sign the
app, but it must be from the same team as the app signing identity.

``--no-sign-installer``
~~~~~~~~~~~~~~~~~~~~~~~

This option is only used when creating a ``.pkg`` installer.

Do not sign the installer. This option can be useful during development and testing.
However, care should be taken using this option for release artefacts, as it may not be
possible to distribute an unsigned installer to others.

``--no-notarize``
~~~~~~~~~~~~~~~~~

Do not submit the application for notarization. By default, apps will be
submitted for notarization unless they have been signed with an ad-hoc
signing identity.

``--resume <submission ID>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apple's notarization server can take a long time to respond - in some cases, hours. When
you submit an app for notarization, the console output of the ``package`` command will
provide you with a submission ID. If the notarization process is interrupted for any
reason (including user intervention), you can use this submission ID with the
``--resume`` option to resume the notarization process for an app.

Application configuration
=========================

The following options can be added to the ``tool.briefcase.app.<appname>.macOS``
section of your ``pyproject.toml`` file.

``entitlement``
~~~~~~~~~~~~~~~

A property whose sub-attributes define keys that will be added to the app's
``Entitlements.plist`` file. Each entry will be converted into a key in the entitlements
file. For example, specifying::

    entitlement."com.apple.vm.networking" = true

will result in an ``Entitlements.plist`` declaration of::

    <key>com.apple.vm.networking</key><true/>

Any Boolean, string, list, or dictionary value can be used as an entitlement value.

All macOS apps are automatically granted the following entitlements by default:

* ``com.apple.security.cs.allow-unsigned-executable-memory``
* ``com.apple.security.cs.disable-library-validation``

You can disable these default entitlements by defining them manually. For example, to
enable library validation, you could add the following to your ``pyproject.toml``::

    entitlement."com.apple.security.cs.disable-library-validation" = false

``info``
~~~~~~~~

A property whose sub-attributes define keys that will be added to the app's
``Info.plist`` file. Each entry will be converted into a key in the entitlements
file. For example, specifying::

    info."NSAppleScriptEnabled" = true

will result in an ``Info.plist`` declaration of::

    <key>NSAppleScriptEnabled</key><true/>

Any Boolean or string value can be used for an ``Info.plist`` value.

``min_os_version``
------------------

The minimum macOS version that the app will support. This controls the value of
``MACOSX_DEPLOYMENT_TARGET`` used when building the app.

``universal_build``
~~~~~~~~~~~~~~~~~~~

A Boolean, indicating whether Briefcase should build a universal app (i.e, an app that
can target both x86_64 and ARM64). Defaults to ``true``; if ``false``, the binary will
only be executable on the host platform on which it was built - i.e., if you build on
an x86_64 machine, you will produce an x86_65 binary; if you build on an ARM64 machine,
you will produce an ARM64 binary.

Permissions
===========

Briefcase cross platform permissions map to a combination of ``info`` and ``entitlement``
keys:

* ``microphone``: an ``info`` entry for ``NSMicrophoneUsageDescription``; and an
  ``entitlement`` of ``com.apple.security.device.audio-input``
* ``camera``: an ``info`` entry for ``NSCameraUsageDescription``; and
  an ``entitlement`` of ``com.apple.security.device.camera``
* ``coarse_location``: an ``info`` entry for ``NSLocationUsageDescription``
  (ignored if ``background_location`` or ``fine_location`` is defined); plus an
  entitlement of ``com.apple.security.personal-information.location``
* ``fine_location``: an ``info`` entry for ``NSLocationUsageDescription``(ignored
  if ``background_location`` is defined); plus an ``entitlement`` of
  ``com.apple.security.personal-information.location``
* ``background_location``: an ``info`` entry for ``NSLocationUsageDescription``;
  plus an ``entitlement`` of ``com.apple.security.personal-information.location``
* ``photo_library``: an ``info`` entry for ``NSPhotoLibraryUsageDescription``; plus an
  ``entitlement`` of ``com.apple.security.personal-information.photos-library``

Platform quirks
===============

Packaging with ``--adhoc-sign``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using the ``--adhoc-sign`` option on macOS produces an app that will be able
to run on your own machine, but won't run on any other computer. In order to
distribute your app to other users, you will need to sign the app with a full
signing identity.

Inconsistent content in non-universal wheels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When building a universal app (i.e., an app that supports both arm64 and x86_64) that
uses binary wheels, Briefcase will look for ``universal2`` multi-architecture wheels by
default. However, if such a wheel is not available, Briefcase will download a
platform-specific wheel for each platform, and then attempt to merge them into a single
binary.

For most wheels, this approach works without difficulty. However, the wheels for some
packages include slightly different content on each platform. NumPy is a notable example
- it includes static libraries (``.a`` files), headers (``.h`` files), and a
``__config__.py`` file that records the configuration options that were used at the time
the wheel was built.

These files cannot be merged, as they either contain fundamentally inconsistent content,
or are in a binary format that doesn't allow for multi-architecture merging.

Briefcase will warn when it finds files that cannot be merged, and will fall back to
copying the version matching the platform where Briefcase has been executed (i.e., if
you're running on an arm64 MacBook, the version from the arm64 wheel will be copied).
You must determine yourself whether this will cause a problem at runtime.

For many forms of content, the files that cannot be merged are **not** used at runtime.
For example, the ``.a`` and ``.h`` files provided by NumPy exist so that code can
statically link against NumPy. They are not needed at runtime by Python code that
imports and uses NumPy.

If you determine that content is not needed at runtime, it can be removed from the app
using the ``cleanup_paths`` configuration option::

    cleanup_paths = [
        "**/app_packages/**/*.a",
        "**/app_packages/**/*.h",
    ]

This will find and purge all ``.a`` content and ``.h`` content in your app's
dependencies. You can add additional patterns to remove other unneeded content.

Requirements cannot be provided as source tarballs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Briefcase *cannot* install packages published as source tarballs into a macOS app, even
if the package is a pure Python package that would produce a ``py3-none-any`` wheel.
This is an inherent limitation in the use of source tarballs as a distribution format.

If you need to install a package in a macOS app that is only published as a source
tarball, you'll need to compile that package into a wheel first. If the package is pure
Python, you can generate a ``py3-none-any`` wheel using ``pip wheel <package name>``. If
the project has a binary component, you will need to consult the documentation of the
package to determine how to compile a wheel.

You can then directly add the wheel file to the ``requires`` definition for your app, or
put the wheel in a folder and add:

.. code-block:: TOML

    requirement_installer_args = ["--find-links", "<path-to-wheel-folder>"]

to your ``pyproject.toml``. This will instruct Briefcase to search that folder for
compatible wheels during the installation process.
