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

Additional files
================

The ``.deb`` template includes a ``LICENSE`` and ``CHANGELOG`` file, with stub
content. When the application is generated from template, Briefcase will look in
the project root folder (i.e., the folder that contains your ``pyproject.toml``)
for files with the same name. If these files are found, they will be copied into
your ``.deb`` project. You should ensure these files are complete and correct
before publishing your app.

The ``.deb`` template also includes an initial draft manfile for your app. This
manfile will be populated with the ``description`` and ``long_description`` of
your app. You may wish to add more details on app usage.

Additional options
==================

The following options can be provided at the command line when producing
Deb packages.

``--target``
~~~~~~~~~~~~

A Docker base image identifier for the Debian-based distribution you want to
target. The identifier will be in the pattern ``<vendor>:<codename>`` (e.g.,
``debian:buster`` or ``ubuntu:jammy``). You can also use the version number in
place of the codename (e.g., ``debian:10`` or ``ubuntu:22.04``). Whichever form
you choose, you should be consistent; no normalization of codename and version
is performed, so ``ubuntu:jammy`` and ``ubuntu:22.04`` will be identified as
different versions (even though they the same version).

You can specify any identifier you want, provided the following conditions are
met:

1. It is a Debian-based distribution;
2. The distribution is still supported by the vendor. If the distribution is
   EOL, ``apt update`` will fail due to expired certificates;
3. The system Python is Python 3.8 or later.

Application configuration
=========================

To generate a ``.deb`` package, an application *must* define a
``long_description``. This ``long_description`` *must not* be a copy of the
short ``description``; nor can the first line of the ``long_description`` match
the ``description``.

The following options can be added to the
``tool.briefcase.app.<appname>.linux.deb`` section of your ``pyproject.toml``
file; if defined in this section, the values will apply for *all* Debian
versions that you target.

If you need to override these settings for a specific target operating system,
you can specify a value in a
``tool.briefcase.app.<appname>.linux.deb.<vendor>.<codename>`` section. Any
vendor-specific definitions will override the generic ``deb`` level definitions.

``python_source``
~~~~~~~~~~~~~~~~~

Describes how the packaged app will obtain a version of Python that will be used
at runtime. This can be one of the following values:

* ``"system"`` - Use the System Python. This produces a ``.deb`` package that is
  smaller, and better integrated with a "default" Debian system; however, it
  means that the version of Python used to run Briefcase *can* be different from
  the version that is used at runtime. Briefcase will check for this discrepancy,
  and warn you if it exists, but it will *not* prevent an app from building.

* ``"deadsnakes"`` - Use a `Deadsnakes <https://github.com/deadsnakes>`__
  version of Python. Deadsnakes is a project that packages all currently
  supported Python versions for all currently supported Ubuntu versions, and
  distributes those packages as a personal package archive (PPA). This allows
  you to produce a packaged app that that will always match the version of
  Python that was used to run Briefcase. However, it will only work on Ubuntu;
  and it places an additional burden on users installing the app, as they must
  manually ensure that they have the Deadsnakes PPA in their system's
  configuration. This can be done by running::

    sudo apt-get update
    sudo apt-get install --no-install-recommends software-properties-common
    sudo apt-add-repository ppa:deadsnakes/ppa

  If this option is selected, and you are building inside Docker, Briefcase will
  ensure that the Docker environment has the Deadsnakes PPA available.

By default, Briefcase uses ``system``.

``system_requires``
~~~~~~~~~~~~~~~~~~~

A list of operating system packages that must be installed for the ``.deb``
build to succeed. If a Docker build is requested, this list will be passed to
the Docker context when building the container for the app build. These entries
should be ``apt`` packages. For example::

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
