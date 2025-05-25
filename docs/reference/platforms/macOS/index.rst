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

General usage of document types is described in the :ref:`document-types`
section. That may be all you need! However, macOS has some additional quirks
that you may need to be aware of when defining document types for your app.

Background
~~~~~~~~~~

First, macOS document types are defined in the ``Info.plist`` file, and the
amount of information that is required depends on whether the document type is a
custom document type or a standard document type already defined by macOS. The
system keeps track of document types using Uniform Type Identifiers (UTIs),
which are strings that uniquely identify a type of data. They are similar to
MIME types, but they form a type *hierarchy* that allows for more complex
relationships between types. For example, PDF files  have the UTI
``com.adobe.pdf``, which conforms to the UTI ``public.data``, indicating that
PDF files are a specific type of data, and also conforms to ``public.content``,
indicating that they are a type of document that can be shared via e.g. Airdrop.
There is a long list of `standard UTIs defined by macOS
<https://developer.apple.com/documentation/uniformtypeidentifiers/system-declared-uniform-type-identifiers>`_.
To find the identifier you'll have to click on the type in the list, and then
look it up under the *Discussion* section.

When you define a document type for your app, you need to provide information
about the type, such as its UTI, the file extensions it supports, and whether
your app can edit or view files of that type. This information is used by macOS
to determine which apps can open which types of files.

If it is a so-called *core type*, then you only need to tell macOS that you
support that type. If it is a not a core type, but a file type defined by
another application, you need to *import* that type definition but also provide
some basic information about the type for the case that the user has not (yet)
installed the official app for that document type. If the document type is
custom for you app, you need to provide all information and *export* the type
definition so that other apps can use it. Briefcase handles all of this for you
automatically, depending on your configuration. You may need to provide whether
the document type is custom for your app, or defined by another app. You can
also change some default assumptions, like whether your app can *edit* the
document type or not. We will discuss this in more detail below.

For reference, the following web pages from Apple provide more background
information, while the implications for Briefcase are described below:

* `Standard UTIs defined by macOS <https://developer.apple.com/documentation/uniformtypeidentifiers/system-declared-uniform-type-identifiers>`_
* `Defining file and data types for your app <https://developer.apple.com/documentation/uniformtypeidentifiers/defining-file-and-data-types-for-your-app>`_
* `Building a document-based app with SwiftUI <https://developer.apple.com/documentation/swiftui/building-a-document-based-app-with-swiftui>`_
* `Uniform Type Identifiers — a reintroduction <https://developer.apple.com/videos/play/tech-talks/10696/?time=549>`_
* `Core Foundation Keys (archived) <https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Articles/CoreFoundationKeys.html>`_

Configuration
~~~~~~~~~~~~~

By defining a MIME type in your app's configuration, Briefcase will
automatically determine whether the type is a core type, a type defined by
another app, or a custom type for your app. It will then generate the
appropriate entries in the ``Info.plist`` file for your app. For example, if you
provide a MIME type of ``application/pdf``, Briefcase will determine that this
is a core type and has a UTI ``com.adobe.pdf``. You can override the generated
values by defining the following keys in your app's configuration:

.. list-table::
  :header-rows: 1
  :widths: 20 40 40

  * - Key
    - Possible Values
    - Description
  * - ``macOS.is_core_type``
    - ``True``, ``False``
    - Whether the document type is a core type defined by macOS.
  * - `macOS.CFBundleTypeRole <https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundledocumenttypes/cfbundletyperole>`_
    - ``Editor``, ``Viewer``, ``Shell``, ``QLGenerator``, ``None``
    - The role of the app with respect to the document type.
  * - `macOS.LSHandlerRank <https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundledocumenttypes/lshandlerrank>`_
    - ``Owner``, ``Alternate``, ``Default``, ``None``
    - The rank of the app with respect to the document type.
  * - `macOS.LSItemContentTypes <https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundledocumenttypes/lsitemcontenttypes>`_
    - A list of strings, each representing a UTI.
    - A list of Uniform Type Identifiers (UTIs) that the app can handle.
  * - `macOS.UTTypeConformsTo <https://developer.apple.com/documentation/BundleResources/Information-Property-List/UTExportedTypeDeclarations/UTTypeConformsTo>`_
    - A list of strings, each representing a UTI.
    - A list of Uniform Type Identifiers (UTIs) that the document type conforms to.

In all cases Briefcase will set the ``macOS.CFBundleTypeRole`` to ``Viewer`` to
indicate that your app can view files of that type. If you want your app to be
able to edit files of that type, you can set the ``macOS.CFBundleTypeRole`` to
``Editor``.

Core Types
----------

When the document type is a core type, Briefcase will automatically set the
``macOS.is_core_type`` key to ``True``, ``macOS.LSItemContentTypes`` to the UTI
of the core type, and ``macOS.LSHandlerRank`` to ``Alternate`` since your app is
not the primary handler for that type. Since core types are defined by macOS,
you do not need to provide  any other information about the type.

Custom Types
------------

When the document type is *not* a core type, Briefcase will set the
``macOS.is_core_type`` key to ``False``, and will set the
``macOS.LSItemContentTypes`` to ``<bundle>.<app_name>.<document_type_id>`` as
the UTI for the document type. You can override this by providing your own
value, e.g. in the case where the document type is defined by *another app* and
you can look up the UTI. The ``macOS.LSHandlerRank`` will be set to ``Owner`` by
default, indicating that your app is the primary handler for that type. If you
want your app to be an alternate handler for the type, e.g. in the case that the
document type is defined by another app, you can set the ``macOS.LSHandlerRank``
to ``Alternate``. Finally, the ``macOS.UTTypeConformsTo`` will be set to
``["public.data", "public.content"]`` by default, indicating that the document
type is a type of data document. If you define an image format, you can conform
to ``public.image``, which itself conforms to ``public.data`` and
``public.content``. Check the list of `standard UTIs defined by macOS
<https://developer.apple.com/documentation/uniformtypeidentifiers/system-declared-uniform-type-identifiers>`_
to find the appropriate UTI for your document type.

Packages
--------

A special case is when the document type is a *package*. That is a directory
that contains files, but is treated as a single file by the operating system.
For example, the ``.app`` bundle is a package, as is the ``.pkg`` installer. If
you want to define such a document type, set ``macOS.UTTypeConformsTo`` to
``["com.apple.package", "public.content"]``, optionally including other UTIs
like ``public.image``.


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
