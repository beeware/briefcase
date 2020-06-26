=============
MSI Installer
=============

An MSI installer is a common format used for the installation, maintenance,
and removal of Windows software. It contains the files to be distributed, along
with metadata supporting the files to be installed, including details such as
registry entries. It includes a GUI installer, and automated generation of
the uninstallation sequence.

Briefcase uses the `WiX Toolset <https://wixtoolset.org/>`__ to build
installers. WiX, in turn, requires that .NET Framework 3.5 is enabled.
To ensure .NET Framework 3.5 is enabled:

    1. Open the Windows Control Panel
    2. Traverse to Programs -> Programs and Features
    3. Select "Turn Windows features On or Off"
    4. Ensure that ".NET framework 3.5 (includes .NET 2.0 and 3.0)" is selected.

Icon format
===========

MSI installers use ``.ico`` format icons.

Splash Image format
===================

MSI installers do not support splash screens or installer images.

Application configuration
=========================

The following options can be added to the
``tool.briefcase.app.<appname>.windows`` section of your ``pyproject.toml``
file.

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

Features
========

Briefcase produced MSI installers do not require elevated privileges for
installation; they default to *per-user* installs. The installer can be
installed for all users using the CLI, with:

.. code-block::

    > msiexec.exe /i <msi-filename> MSIINSTALLPERUSER=""
