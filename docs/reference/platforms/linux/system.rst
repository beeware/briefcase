======================
Native System Packages
======================

+--------+-------+---------+--------+---+-----+--------+-----+-------+
| Host Platform Support (:ref:`platform-support-key`)                |
+--------+-------+---------+--------+---+-----+--------+-----+-------+
| macOS          | Windows              | Linux                      |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+
| x86‑64 | arm64 | x86 | x86‑64 | arm64 | x86 | x86‑64 | arm | arm64 |
+========+=======+=====+========+=======+=====+========+=====+=======+
| |y|    | |y|   |     |        |       | |v| | |f|    | |v| | |v|   |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+

All modern Linux distributions have a native format for distributing packages
that are integrated into their overall operating system:

* ``.deb``, used by Debian, Ubuntu, Mint (and others)
* ``.rpm``, used by Red Hat, Fedora, CentOS, AlmaLinux, openSUSE (and others)
* ``.pkg.tar.zst``, used by Arch Linux and Manjaro Linux

The Briefcase ``system`` backend provides a way to build your app in these
system package formats.

.. admonition:: Not all Linux distributions are supported!

    Briefcase cannot reliably identify *every* Linux vendor. If your Linux distribution
    isn't being identified (or isn't being identified correctly), please `open a ticket
    <https://github.com/beeware/briefcase/issues>`__ with the contents of your
    ``/etc/os-release`` file.

The packaged app includes a stub binary, so that the app will appear in process
lists using your app's name. It also includes a FreeDesktop registration so the
app will appear in system menus.

When installed from a Briefcase-produced system package, the app will use the
system Python install, and the standard library provided by the system. However,
the app will be isolated from any packages that have been installed at a system
level.

As the app uses the system Python, system packages are highly dependent on the
distribution version. It is therefore necessary to build a different system
package for every distribution you want to target. To help simplify this
process, Briefcase uses Docker to provide build environments. Using these Docker
environments, it is possible to build a system package for any target
distribution and version, regardless of the host distribution and version - that
is, you can build a Debian Buster package on an Ubuntu 20.04 machine, or an
Ubuntu 22.04 package on a RHEL8 machine.

The usage of the system Python also means that system packages are different
from most other Briefcase-packaged apps. On other target platforms (macOS and
Windows apps, Linux AppImage, etc), the version of Python used to run Briefcase
will be the version of Python used by the bundled app. However, when building a
system package, Briefcase will use the operating system's Python3 installation
for system packages, regardless of the host Python version. This means you
will need to perform additional platform testing to ensure that your app is
compatible with that version of Python.

Icon format
===========

Deb packages uses ``.png`` format icons. An application must provide icons in
the following sizes:

* 16px
* 32px
* 64px
* 128px
* 256px
* 512px

Splash Image format
===================

Linux System packages do not support splash screens or installer images.

Additional files
================

The Linux system app template includes a ``LICENSE`` and ``CHANGELOG`` file,
with stub content. When the application is generated from template, Briefcase
will look in the project root folder (i.e., the folder that contains your
``pyproject.toml``) for files with the same name. If these files are found, they
will be copied into your project. You should ensure these files are complete and
correct before publishing your app.

The Linux system app template also includes an initial draft manfile for your
app. This manfile will be populated with the ``description`` and
``long_description`` of your app. You may wish to add more details on app usage.

Additional options
==================

The following options can be provided at the command line when producing
Deb packages:

``--target``
~~~~~~~~~~~~

A Docker base image identifier for the Linux distribution you want to target.
The identifier will be in the pattern ``<vendor>:<codename>`` (e.g.,
``debian:buster`` or ``ubuntu:jammy``). You can also use the version number in
place of the code name (e.g., ``debian:10``, ``ubuntu:22.04``, or
``fedora:37``). Whichever form you choose, you should be consistent; no
normalization of code name and version is performed, so ``ubuntu:jammy`` and
``ubuntu:22.04`` will be identified as different versions (even though they the
same version).

You can specify any identifier you want, provided the distribution is still
supported by the vendor, and system Python is Python 3.8 or later.

The following Linux vendors are known to work as Docker targets:

* Debian (e.g., ``debian:bullseye`` or ``debian:11``)
* Ubuntu (e.g., ``ubuntu:jammy`` or ``ubuntu:22.04``)
* Fedora (e.g, ``fedora:37``)
* AlmaLinux (e.g., ``almalinux:9``)
* Red Hat Enterprise Linux (e.g., ``redhat/ubi9:9``)
* openSUSE Tumbleweed (e.g., ``"opensuse/tumbleweed:latest"``)
* Arch Linux (e.g., ``archlinux:latest``)
* Manjaro Linux (e.g., ``manjarolinux/base:latest``)

Application configuration
=========================

The following options can be added to the
``tool.briefcase.app.<appname>.linux.system`` section of your ``pyproject.toml``
file; if defined in this section, the values will apply for *all* Linux
distributions for which you build packages.

If you need to override these settings for a specific target vendor, or for a
specific distribution version, you can provide increasingly specific sections for
vendor and version information. Each distribution is identified by:

* Vendor base (e.g., ``debian``, ``rhel``, ``arch``, ``suse``)
* Vendor (e.g, ``debian``, ``ubuntu``, ``rhel``, ``fedora``, ``opensuse-tumbleweed``,
  ``arch``, ``manjaro``). The vendor identifier *may* be the same as the vendor base
  (e.g, in the case of Debian, Red Hat, or Arch)
* Code name (e.g., a version number, or ``jammy``).

For example, a full configuration for ``myapp`` running on Ubuntu 22.04 (jammy)
would consist of the following sections:

* ``tool.briefcase.app.myapp`` providing global configuration options
* ``tool.briefcase.app.myapp.linux`` providing definitions common to *all* Linux
  packaging backends
* ``tool.briefcase.app.myapp.linux.system`` providing definitions for all Linux
  system package targets
* ``tool.briefcase.app.myapp.linux.system.debian`` providing definitions common
  to all Debian-based packaging targets
* ``tool.briefcase.app.myapp.linux.system.ubuntu`` providing definitions common
  to all Ubuntu-based packaging targets
* ``tool.briefcase.app.myapp.linux.system.ubuntu.jammy`` providing definitions
  specific to for Ubuntu 22.04 (Jammy).

These configurations will be merged at runtime; any version-specific definitions
will override the generic vendor definitions; any vendor definitions will
override the vendor-base definitions; and any vendor-base definitions will
override generic system package definitions.

``system_requires``
~~~~~~~~~~~~~~~~~~~

A list of operating system packages that must be installed for the system package
build to succeed. If a Docker build is requested, this list will be passed to
the Docker context when building the container for the app build. These entries
should be the format the target Linux distribution will accept. For example, if you're
using a Debian-derived distribution, you might use::

    system_requires = ["libgirepository1.0-dev", "libcairo2-dev"]

to make the GTK GI and Cairo operating system development packages available
to your app. However, if you're on a RedHat-derived distribution, you would use::

    system_requires = ["gobject-introspection-devel", "python3-cairo-devel"]

If you see errors during ``briefcase build`` of the form::

    Could not find dependency: libSomething.so.1

but the app works under ``briefcase dev``, the problem may be an incomplete
``system_requires`` definition. The ``briefcase build`` process generates
a new environment that is completely isolated from your development
environment, so if your app has any operating system dependencies, they
*must* be listed in your ``system_requires`` definition.

``system_requires`` are the packages required at *build* time. To specify
*runtime* system requirements, use the ``system_runtime_requires`` setting.

``system_runtime_requires``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A list of system packages that your app requires at *runtime*. These will be
closely related to the ``system_requires`` setting, but will likely be
different; most notably, you will probably need ``-dev`` packages at build time,
but non ``-dev`` packages at runtime.

``system_runtime_requires`` should be specified as system package requirements;
they can optionally include version pins. Briefcase will automatically include
the dependencies needed for Python. For example::

    system_runtime_requires = ["libgtk-3-0 (>=3.14)", "libwebkit2gtk-4.0-37"]

will specify that your app needs Python 3, a version of ``libgtk >= 3.14``, and any
version of ``libwebkit2gtk``.

Any problems with installing or running your system package likely indicate an
issue with your ``system_runtime_requires`` definition.

``system_section``
~~~~~~~~~~~~~~~~~~

When an application is published as a ``.deb`` file, Debian requires that you
specify a "section", describing a classification of the application area. The
template will provide a default section of ``utils``; if you want to override
that default, you can specify a value for ``system_section``. For details on the
allowed values for ``system_section``, refer to the `Debian Policy Manual
<https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-section>`__.

``dockerfile_extra_content``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Any additional Docker instructions that are required to configure the container
used to build your Python app. For example, any dependencies that cannot be
configured with ``apt-get`` could be installed. ``dockerfile_extra_content`` is
string literal that will be added verbatim to the end of the project Dockerfile.

Any Dockerfile instructions added by ``dockerfile_extra_content`` will be
executed as the ``brutus`` user, rather than the ``root`` user. If you need to
perform container setup operations as ``root``, switch the container's user to
``root``, perform whatever operations are required, then switch back to the
``brutus`` user - e.g.::

    dockerfile_extra_content = """
    RUN <first command run as brutus>

    USER root
    RUN <second command run as root>

    USER brutus
    """
