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

.. _macOS-document-types:

Document types
==============

Internally, macOS uses Uniform Type Identifiers (UTIs) to track document types. UTIs are
strings that uniquely identify a type of data. They are similar to MIME types, but they
form a type hierarchy that allows for more complex relationships between types. For
example, PDF files have the UTI ``com.adobe.pdf``, which conforms to the UTI
``public.data``, indicating that PDF files are a specific type of data, and also
conforms to ``public.content``, indicating that they are a type of document that can be
shared via e.g. Airdrop. There is a long list of `standard UTIs defined by macOS
<https://developer.apple.com/documentation/uniformtypeidentifiers/system-declared-uniform-type-identifiers>`_.

These UTIs are then used to declare document types in an application's ``Info.plist``.
Briefcase will determine an appropriate declarations based on the MIME type that has
been provided (or generated) for a document type. However, there are also some
macOS-specific configuration items that can be used to override this default behavior
to control how document types are presented on macOS.

Configuration options
~~~~~~~~~~~~~~~~~~~~~

The following macOS-specific configuration keys can be used in a document type
declaration:

``macOS.CFBundleTypeRole``
--------------------------

`CFBundleTypeRole
<https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundledocumenttypes/cfbundletyperole>`_
declares the role the application plays with respect to the document type. Valid values
are ``Editor``, ``Viewer``, ``Shell``, ``QLGenerator``, and ``None``.

Briefcase will default to a role of ``Viewer`` for all document types.

``macOS.LSHandlerRank``
-----------------------

`LSHandlerRank
<https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundledocumenttypes/lshandlerrank>`_
defines the relative priority of this application when it comes to determining which
application should open an application. Valid values are ``Owner``, ``Alternate``,
``Default`` and ``None``.

Briefcase will default to a role of ``Alternate`` for any known MIME type, and ``Owner``
for any custom MIME type.

``macOS.LSItemContentTypes``
----------------------------

`LSItemContentTypes <https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundledocumenttypes/lsitemcontenttypes>`_ define the
UTI content types that the app can handle.

Briefcase defaults to the the registered UTI type for known MIME types. It will construct a UTI of the form ``<bundle id>.<app name>.<document type id>`` (e.g., ``org.beeware.helloworld.document``) for unknown MIME types.

Although macOS technically allows an application to support multiple UTIs per document types, Briefcase can only assign a single content type. The value of ``macOS.LSItemContentTypes`` must be a string, or a list containing a single value.

``macOS.UTTypeConformsTo``
--------------------------

`UTTypeConformsTo
<https://developer.apple.com/documentation/BundleResources/Information-Property-List/UTExportedTypeDeclarations/UTTypeConformsTo>`_
defines the list of UTIs that the document type conforms to. Each entry is a string.

Briefcase will assume a default of ``["public.data", "public.content"]`` for unknown
MIME types. The value is not used for known mime types (as the operating system knows
the conforming types).

``macOS.is_core_type``
----------------------

A Boolean, used to explicitly declare a content type as a core type. This flag is used
to determine whether a ``UTImportedTypeDeclarations`` entry is required in macOS app
metadata.

You shouldn't need to set this value. Briefcase is able to determine whether a type is
core or not based using data provided by the operating system.

Packages
~~~~~~~~

macOS provides for document types that are *packages*. A package document is structured
as a directory on disk, but presents to the user as a single icon. An ``.app`` bundle is
an example of a package document type.

To define a package type, set ``macOS.UTTypeConformsTo`` to ``["com.apple.package",
"public.content"]``. If other UTI types apply, they can also be added to this list.

Further customization
~~~~~~~~~~~~~~~~~~~~~

For more details on macOS document type declarations, see the following web pages from
Apple provide more background information. They may be helpful in determining how to
expose content types for your application:

 * `Defining file and data types for your app
   <https://developer.apple.com/documentation/uniformtypeidentifiers/defining-file-and-data-types-for-your-app>`_
 * `Uniform Type Identifiers — a reintroduction
   <https://developer.apple.com/videos/play/tech-talks/10696/?time=549>`_
 * `Core Foundation Keys (archived)
   <https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Articles/CoreFoundationKeys.html>`_

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

Use of iCloud-synchronized folders
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

iCloud stores and maintains metadata on some content stored in iCloud-synchronized
folders. Unfortunately, this metadata prevents apps from being signed and notarized, and
app signing is a requirement for all apps on macOS. As a result, Briefcase cannot be
used to generate macOS apps in a folder that is synchronized with iCloud.

This most commonly affects the `Documents` and `Desktop` folders (and subfolders), but
can affect other locations if they are synchronized with iCloud.

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
