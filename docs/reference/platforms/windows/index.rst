=======
Windows
=======

.. toctree::
   :hidden:

   app
   visualstudio

+--------+-------+---------+--------+---+-----+--------+-----+-------+
| Host Platform Support (:ref:`platform-support-key`)                |
+--------+-------+---------+--------+---+-----+--------+-----+-------+
| macOS          | Windows              | Linux                      |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+
| x86‑64 | arm64 | x86 | x86‑64 | arm64 | x86 | x86‑64 | arm | arm64 |
+========+=======+=====+========+=======+=====+========+=====+=======+
|        |       |     | |f|    |       |     |        |     |       |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+

Briefcase supports two output formats for Windows apps:

* A :doc:`./app` with a pre-compiled binary; and
* A :doc:`./visualstudio` which can be used to build an app with a customized
  binary.

The default output format for Windows is a :doc:`./app`.

Configuration options between the :doc:`./app` and :doc:`./visualstudio` formats are
identical.

.. _windows-prerequisites:

Prerequisites
=============

Briefcase requires installing Python 3.9+.

Packaging format
================

Briefcase supports two packaging formats for a Windows app:

1. As an MSI installer (the default output of ``briefcase package windows``, or by using
   ``briefcase package windows -p msi``); or
2. As a ZIP file containing all files needed to run the app (by using ``briefcase
   package windows -p zip``).

Briefcase uses the `WiX Toolset <https://www.firegiant.com/wixtoolset/>`__ to build an
MSI installer for a Windows app.

Icon format
===========

Windows apps installers use multi-format ``.ico`` icons; these icons should
contain images in the following sizes:

* 16px
* 32px
* 48px
* 64px
* 256px

Windows Apps do not support splash screens or installer images.

Additional options
==================

The following options can be provided at the command line when packaging
Windows apps.

``--file-digest <digest>``
~~~~~~~~~~~~~~~~~~~~~~~~~~

The digest algorithm to use for code signing files in the project. Defaults to
``sha256``.

``--use-local-machine-stores``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the certificate for code signing is assumed to be in the Current
User's certificate stores. Use this flag to indicate the certificate is in the
Local Machine's certificate stores.

``--cert-store <store>``
~~~~~~~~~~~~~~~~~~~~~~~~

The internal Windows name for the certificate store containing the certificate
for code signing. Defaults to ``My``.

Common Stores:

+--------------------------------------------+------------------+
| Personal                                   | My               |
+--------------------------------------------+------------------+
| Intermediate Certification Authorities     | CA               |
+--------------------------------------------+------------------+
| Third-Party Root Certification Authorities | AuthRoot         |
+--------------------------------------------+------------------+
| Trusted People                             | TrustedPeople    |
+--------------------------------------------+------------------+
| Trusted Publishers                         | TrustedPublisher |
+--------------------------------------------+------------------+
| Trusted Root Certification Authorities     | Root             |
+--------------------------------------------+------------------+

``--timestamp-url <url>``
~~~~~~~~~~~~~~~~~~~~~~~~~

The URL of the Timestamp Authority server to timestamp the code signing.
Defaults to ``http://timestamp.digicert.com``.

``--timestamp-digest <url>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The digest algorithm to request the Timestamp Authority server uses for the
timestamp for code signing. Defaults to ``sha256``.

Application configuration
=========================

.. currentmodule:: windows

The following options can be added to the
``tool.briefcase.app.<appname>.windows`` section of your ``pyproject.toml``
file.

.. attribute:: installer_path

The name of a directory in the package bundle that can be used to store post-install and
pre-uninstall scripts. Defaults to ``_installer``.

.. attribute:: post_install_script

A path, relative to the project root, to a Windows ``.bat`` file that will be executed
after the installer content has been unpacked. Only used for MSI packaging.

.. attribute:: pre_uninstall_script

A path, relative to the project root, to a Windows ``.bat`` file that will be executed
before the installed content is removed by uninstalling the app. Only used for MSI
packaging.

.. attribute:: system_installer

Controls whether the app will be installed as a per-user or per-machine app.
Per-machine apps are "system" apps, and require admin permissions to run the
installer; however, they are installed once and shared between all users on a
computer.

If ``true`` the installer will attempt to install the app as a per-machine app,
available to all users. If ``false``, the installer will install as a per-user
app. If undefined the installer will ask the user for their preference.

.. attribute:: use_full_install_path

Controls whether the app will be installed using a path which includes both the
application name *and* the company or developer's name. If ``true`` (the
default), the app will be installed to ``Program Files\<Author Name>\<Project
Name>``. If ``false``, it will be installed to ``Program Files\<Project Name>``.
Using the full path makes sense for larger companies with multiple applications,
but less so for a solo developer.

.. attribute:: version_triple

Python and Briefcase allow any valid `PEP440 version number
<https://peps.python.org/pep-0440/>`_ as a :attr:`version` specifier. However, MSI
installers require a strict integer triple version number. Many
PEP440-compliant version numbers, such as "1.2", "1.2.3b3", and "1.2.3.4", are
invalid for MSI installers.

Briefcase will attempt to convert your :attr:`version` into a valid MSI value by
extracting the first three parts of the main series version number (excluding
pre, post and dev version indicators), padding with zeros if necessary:

    * ``1.2`` becomes ``1.2.0``
    * ``1.2b4`` becomes ``1.2.0``
    * ``1.2.3b3`` becomes ``1.2.3``
    * ``1.2.3.4`` becomes ``1.2.3``.

However, if you need to override this default value, you can define
:attr:`version_triple` in your app settings. If provided, this value will be used in the
MSI configuration file instead of the auto-generated value.

Installer options
~~~~~~~~~~~~~~~~~

.. currentmodule:: install_option

Windows MSI installers are able to present a panel of optional features to the user
as part of the installation process. These features are binary flags which can then be
used by a post-install script to perform additional installation behaviors.

Installer options are defined using a TOML array of tables - each option is in a
group named ``[[ toga.briefcase.app.<app name>.install_option ]]``, which must
define the following keys:

.. attribute:: name

An identifier for the option. This name must be a valid Python identifier; the list of
options specified for an app must be unique when converted into upper case (i.e., you
cannot have ``value`` and ``VALUE`` in the same configuration).

.. attribute:: title

A short human-readable label describing the option, as a string.

.. attribute:: description

A longer description of the purpose of the option, as a string.

.. attribute:: default

A Boolean describing the initial value of the option in the GUI. If not provided,
defaults to ``False``.

Using installer options
-----------------------

When an installer option is defined, the value of the option will be made available to
the post-install script as an environment variable whose name is the capitalized version
of the option name. If your installer defines an option with a name of ``foo``, an
environment variable of ``OPTION_FOO`` will be defined, with a value of 1 if the option
has been selected by the user, and 0 if the option has not been selected. The
``ALLUSERS`` environment variable will also be set; its value will be 1 if the app has
been installed for all users, or 0 if it has only been installed for the current user.

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
flagged as coming from an unverified publisher. This may limit who is able to
install your app.

Tkinter is not available
~~~~~~~~~~~~~~~~~~~~~~~~

Briefcase uses the official `Python.org Windows Embeddable package
<https://docs.python.org/3/using/windows.html#windows-embeddable>`__ to provide Python
binaries for the Windows app. This embeddable distribution is missing some standard
library modules that would be part of a normal Python.org install - most notably
``tkinter``. This is due to the difficulty in distributing the Tk libraries needed by
Tkinter in a way that is compatible with the Windows embedded binary format.
