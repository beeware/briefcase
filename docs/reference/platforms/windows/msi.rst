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

Image format
============

MSI installers do not support splash screens or installer images.
