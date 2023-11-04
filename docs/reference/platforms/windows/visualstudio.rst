=====================
Visual Studio project
=====================

+--------+-------+---------+--------+---+-----+--------+-----+-------+
| Host Platform Support (:ref:`platform-support-key`)                |
+--------+-------+---------+--------+---+-----+--------+-----+-------+
| macOS          | Windows              | Linux                      |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+
| x86‑64 | arm64 | x86 | x86‑64 | arm64 | x86 | x86‑64 | arm | arm64 |
+========+=======+=====+========+=======+=====+========+=====+=======+
|        |       |     | |f|    |       |     |        |     |       |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+

Briefcase supports creating a full Visual Studio project for a Windows App. This
project can then be used to build the stub app binary with the ``briefcase
build`` command, or directly from Visual Studio.

Building the Visual Studio project requires that you install Visual Studio 2022
or later. Visual Studio 2022 Community Edition `can be downloaded for free from
Microsoft <https://visualstudio.microsoft.com/vs/community/>`__. You can also
use the Professional or Enterprise versions if you have them.

Briefcase will auto-detect the location of your Visual Studio installation,
provided one of the following three things are true:

1. You install Visual Studio in the standard location in your Program Files folder.
2. ``MSBuild.exe`` is on your path.
3. You define the environment variable ``MSBUILD`` that points at the location of
   your ``MSBuild.exe`` executable.

When you install Visual Studio, there are many optional components. You should
ensure that you have installed the following:

* .NET Desktop Development
  - All default packages
* Desktop Development with C++
  - All default packages
  - C++/CLI support for v143 build tools

Packaging format
================

Briefcase supports two packaging formats for a Windows app:

1. As an MSI installer (the default output of ``briefcase package windows
   VisualStudio``, or by using ``briefcase package windows VisualStudio -p msi``); or
2. As a ZIP file containing all files needed to run the app (by using ``briefcase
   package windows VisualStudio -p zip``).

Briefcase uses the `WiX Toolset <https://wixtoolset.org/>`__ to build an MSI
installer for a Windows App. WiX, in turn, requires that .NET Framework 3.5 is
enabled. To ensure .NET Framework 3.5 is enabled:

1. Open the Windows Control Panel
2. Traverse to Programs -> Programs and Features
3. Select "Turn Windows features On or Off"
4. Ensure that ".NET framework 3.5 (includes .NET 2.0 and 3.0)" is selected.

Icon format
===========

Windows apps installers use multi-format ``.ico`` icons; these icons should
contain images in the following sizes:

* 16px
* 32px
* 48px
* 64px
* 256px

Splash Image format
===================

Windows Apps do not support splash screens or installer images.

Additional options
==================

The following options can be provided at the command line when packaging
Windows apps.

.. include:: signing_options.rst

Application configuration
=========================

The following options can be added to the
``tool.briefcase.app.<appname>.windows`` section of your ``pyproject.toml``
file.

``system_installer``
~~~~~~~~~~~~~~~~~~~~

Controls whether the app will be installed as a per-user or per-machine app.
Per-machine apps are "system" apps, and require admin permissions to run the
installer; however, they are installed once and shared between all users on a
computer.

If ``true`` the installer will attempt to install the app as a per-machine app,
available to all users. If ``false``, the installer will install as a per-user
app. If undefined the installer will ask the user for their preference.

``use_full_install_path``
~~~~~~~~~~~~~~~~~~~~~~~~~

Controls whether the app will be installed using a path which includes both the
application name *and* the company or developer's name. If ``true`` (the
default), the app will be installed to ``Program Files\<Author Name>\<Project
Name>``. If ``false``, it will be installed to ``Program Files\<Project Name>``.
Using the full path makes sense for larger companies with multiple applications,
but less so for a solo developer.

``version_triple``
~~~~~~~~~~~~~~~~~~

Python and Briefcase allow any valid `PEP440 version number
<https://peps.python.org/pep-0440/>`_ as a ``version`` specifier. However, MSI
installers require a strict integer triple version number. Many
PEP440-compliant version numbers, such as "1.2", "1.2.3b3", and "1.2.3.4", are
invalid for MSI installers.

Briefcase will attempt to convert your ``version`` into a valid MSI value by
extracting the first three parts of the main series version number (excluding
pre, post and dev version indicators), padding with zeros if necessary:

    * ``1.2`` becomes ``1.2.0``
    * ``1.2b4`` becomes ``1.2.0``
    * ``1.2.3b3`` becomes ``1.2.3``
    * ``1.2.3.4`` becomes ``1.2.3``.

However, if you need to override this default value, you can define
``version_triple`` in your app settings. If provided, this value will be used
in the MSI configuration file instead of the auto-generated value.

Platform quirks
===============

Use caution with ``--update-support``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Care should be taken when using the ``--update-support`` option to the
``update``, ``build`` or ``run`` commands. Support packages in Windows apps are
overlaid with app content, so it isn't possible to remove all old support files
before installing new ones.

Briefcase will unpack the new support package without cleaning up existing
support package content. This *should* work; however, ensure a reproducible
release artefacts, it is advisable to perform a clean app build before release.

Packaging with ``--adhoc-sign``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using the ``--adhoc-sign`` option on Windows results in no signing being
performed on the packaged app. This will result in your application being
flagged as coming from an unverified publisher. This may limit who can (or is
willing to) install your app.
