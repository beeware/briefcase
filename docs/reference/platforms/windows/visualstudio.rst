=====================
Visual Studio project
=====================

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
   your ``MSBuild.exe`` executable

When you install Visual Studio, there are many optional components. You should
ensure that you have installed the following:

    * .NET Desktop Development
      - All default packages
    * Desktop Development with C++
      - All default packages
      - C++/CLI support for v143 build tools

Briefcase uses the `WiX Toolset <https://wixtoolset.org/>`__ to build an MSI
installer for a Windows App. WiX, in turn, requires that .NET Framework 3.5 is
enabled. To ensure .NET Framework 3.5 is enabled:

    1. Open the Windows Control Panel
    2. Traverse to Programs -> Programs and Features
    3. Select "Turn Windows features On or Off"
    4. Ensure that ".NET framework 3.5 (includes .NET 2.0 and 3.0)" is selected.

Icon format
===========

Windows apps installers use multiformat ``.ico`` icons; these icons should
contain images in the following sizes:

* 16x16
* 32x32
* 48x48
* 64x64
* 256x256

Splash Image format
===================

Windows Apps do not support splash screens or installer images.

Application configuration
=========================

The following options can be added to the
``tool.briefcase.app.<appname>.windows`` section of your ``pyproject.toml``
file.

``system_installer``
--------------------

Controls whether the app will be installed as a per-user or per-machine app.
Per-machine apps are "system" apps, and require admin permissions to run the
installer; however, they are installed once and shared between all users on a
computer.

If ``true`` the installer will attempt to install the app as a per-machine app,
available to all users. If ``false``, the installer will install as a per-user
app. If undefined the installer will ask the user for their preference.

``version_triple``
------------------

Python and Briefcase allow any valid `PEP440 version number
<https://www.python.org/dev/peps/pep-0440/>`_ as a ``version`` specifier.
However, MSI installers require a strict integer triple version number. Many
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
