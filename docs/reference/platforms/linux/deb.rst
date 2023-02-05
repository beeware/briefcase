====================
Debian .deb packages
====================

Debian, and Debian-based Linux distributions like Ubuntu or Linux Mint, use
the ``.deb`` format for system packages. The Briefcase ``deb`` backend provides
a way to build your app as a ``.deb`` package.

The packaged app includes a stub binary, so that the app will appear in process
lists using your app's name. It also includes a FreeDesktop registration so the
app will appear in system menus.

When installed from a ``.deb``, the app will use the system Python install,
and the standard library provided by the system. However, the app will be
isolated from any packages that have been installed at a system level.

As the app uses the system python, Deb packages are highly dependent on the
distribution version. It is therefore necessary to build a ``.deb`` package for
every Debian-based distribution you want to target. To help simplify this
process, Briefcase uses Docker to provide build environments. Using these Docker
environments, it is possible to build a ``.deb`` package for any target
distribution and version, regardless of the host distribution and version - that
is, you can build a Debian Buster package on an Ubuntu 20.04 machine, or on a
RHEL8 machine.

The usage of the system Python also means that ``.deb`` packages are different
from most other Briefcase-packaged apps. On other target platforms (macOS and
Windows apps, Linux AppImage, etc), the version of Python used to run Briefcase
will be the version of Python used by the bundled app. However, when building a
``.deb`` package, Briefcase will use the operating system's Python3 installation
for ``.deb`` packages, regardless of the host Python version. This means you
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

Deb packages do not support splash screens or installer images.

Additional options
==================

The following options can be provided at the command line when producing
Deb packages.

``--no-docker``
~~~~~~~~~~~~~~~

Use native execution, rather than using Docker to start a container.
To use this option, you must:

1. Be on a Debian-based platform; and
2. Have the ``dpkg-dev`` tools installed.

Using this option, you can only build a ``.deb`` package for your host system.
Specifying ``--no-docker`` is mutually exclusive with ``--target``.

``--target``
~~~~~~~~~~~~

A Docker base image identifier for the Debian-based distribution you want to
target. The identifier will be in the pattern ``<vendor>:<codename>`` (e.g.,
``debian:buster`` or ``ubuntu:jammy``). You can also use the version number in
place of the codename (e.g., ``debian:10`` or ``ubuntu:22.04``). Whichever form
you choose, you should be consistent; no normalization of codename and version
is performed, so ``ubuntu:jammy`` and ``ubuntu:22.04`` will be identified as
different versions (even though they the same version).

You can specify any identifier you want, provided the following conditions are met:

1. It is a Debian-based distribution.
2. The distribution is still supported by the vendor. If the distribution is
   EOL, ``apt update`` will fail due to expired certificates.
2. The system Python is Python 3.8 or later.

Specifying ``--target`` is mutually exclusive with ``--no-docker``.

Application configuration
=========================

The following options can be added to the
``tool.briefcase.app.<appname>.linux.deb`` section of your ``pyproject.toml``
file; if defined in this section, the values will apply for *all* Debian
versions that you target.

If you need to override these settings for a specific target operating system,
you can specify a value in a
``tool.briefcase.app.<appname>.linux.deb.<vendor>.<codename>`` section. Any
vendor-specific definitions will override the generic ``deb`` level definitions.

``system_requires``
~~~~~~~~~~~~~~~~~~~

A list of operating system packages that must be installed for the ``.deb``
build to succeed. If a Docker build is requested, this list will be passed to
the Docker context when building the container for the app build. These entries
should be ``apt`` packages. For example,

    system_requires = ["libgirepository1.0-dev", "libcairo2-dev"]

would make the GTK GI and Cairo operating system development packages available
to your app.

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

``system_runtime_requires`` should be specified as system package requirements; they can
optionally include version pins. Briefcase will automatically include the
dependency on Python. For example::

    system_runtime_requires = ["libgtk-3-0 (>=3.14)", "libwebkit2gtk-4.0-37"]

will specify that your app needs Python3, a version of libgtk >= 3.14, and any
version of libwebkit2gtk.

Any problems with installing or running your .deb package likely indicate an
issue with your ``system_runtime_requires`` definition.

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
