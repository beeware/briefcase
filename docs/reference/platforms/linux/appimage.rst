========
AppImage
========

+--------+-------+---------+--------+---+-----+--------+-----+-------+
| Host Platform Support (:ref:`platform-support-key`)                |
+--------+-------+---------+--------+---+-----+--------+-----+-------+
| macOS          | Windows              | Linux                      |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+
| x86‑64 | arm64 | x86 | x86‑64 | arm64 | x86 | x86‑64 | arm | arm64 |
+========+=======+=====+========+=======+=====+========+=====+=======+
| |v|    | |v|   |     |        |       | |v| | |v|    | |v| | |v|   |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+

.. admonition:: Best effort support

    AppImage has a number of significant issues building images for GUI apps. It is
    incompatible with the use of binary wheels, and the use of an older Linux base image
    for compatibility purposes is incompatible with using modern GUI frameworks. Even
    when a GUI toolkit *can* be installed, the AppImage packaging process frequently
    introduces bugs related to DBus integration or libraries like WebKit2 that use
    subprocesses.

    Briefcase provides an AppImage backend for historical reasons, but we strongly
    discourage the use of AppImages for distribution. We maintain unit test coverage for
    the AppImage backend, but we do not build AppImages as part of our release process.
    We will accept bug reports related to AppImage support, and we will merge PRs that
    address AppImage support, but the core team does not consider addressing AppImage
    bugs a priority.

    If you need to distribute a Linux app, :doc:`System packages <./system>` or
    :doc:`Flatpaks <./flatpak>` are much more reliable options.

`AppImage <https://appimage.org>`__ provides a way for developers to provide
"native" binaries for Linux users. It allow packaging applications for any
common Linux based operating system, including Ubuntu, Debian, Fedora, and more.
AppImages contain all the dependencies that cannot be assumed to be part of each
target system, and will run on most Linux distributions without further
modifications. Briefcase uses `Linuxdeploy
<https://github.com/linuxdeploy/linuxdeploy>`__ to build the AppImage in the
correct format.

Packaging binaries for Linux is complicated, because of the inconsistent
library versions present on each distribution. An AppImage can be executed on
*any* Linux distribution with a version of ``libc`` greater than or equal the
version of the distribution where the AppImage was created.

To ensure that an application is built in an environment that is as compatible
as possible, Briefcase builds AppImages inside Docker. The Docker base image
used by Briefcase can be configured to any `manylinux
<https://github.com/pypa/manylinux>`__ base using the ``manylinux`` application
configuration option; if ``manylinux`` isn't specified, it falls back to an Ubuntu
18.04 base image. While it is *possible* to build AppImages without Docker, it
is highly recommended that you do not, as the resulting AppImages will not be as
portable as they could otherwise be.

.. note::

    AppImage works by attempting to autodetect all the libraries that an
    application requires, copying those libraries into a distribution, and
    manipulating them to reflect their new locations. This approach *can* work
    well... but it is also prone to major problems. Python apps (which load
    their dependencies dynamically) are particularly prone to exposing those
    flaws.

    Briefcase makes a best-effort attempt to use the AppImage tools to build
    a binary, but sometimes, the problem lies with AppImage itself. If you
    have problems with AppImage binaries, you should first check whether the
    problem is a limitation with AppImage.

Icon format
===========

AppImages use ``.png`` format icons. An application must provide icons in
the following sizes:

* 16px
* 32px
* 64px
* 128px
* 256px
* 512px

Splash Image format
===================

AppImages do not support splash screens or installer images.

Additional options
==================

The following options can be provided at the command line when producing
AppImages.

``--no-docker``
~~~~~~~~~~~~~~~

Use native execution, rather than using Docker to start a container.

Application configuration
=========================

The following options can be added to the
``tool.briefcase.app.<appname>.linux.appimage`` section of your
``pyproject.toml`` file.

``manylinux``
~~~~~~~~~~~~~

The `manylinux <https://github.com/pypa/manylinux>`__ tag to use as a base image
when building the AppImage. Should be one of:

* ``manylinux1``
* ``manylinux2010``
* ``manylinux2014``
* ``manylinux2_24``
* ``manylinux2_28``

New projects will default to ``manylinux2014``. If an application doesn't specify
a ``manylinux`` value, ``ubuntu:18.04`` will be used as the base image.

``manylinux_image_tag``
~~~~~~~~~~~~~~~~~~~~~~~

The specific tag of the ``manylinux`` image to use. Defaults to ``latest``.

``system_requires``
~~~~~~~~~~~~~~~~~~~

A list of operating system packages that must be installed for the AppImage
build to succeed. If a Docker build is requested, this list will be passed to
the Docker context when building the container for the app build. By default,
entries should be Ubuntu 18.04 ``apt`` package requirements. For example::

    system_requires = ['libgirepository1.0-dev', 'libcairo2-dev']

would make the GTK GI and Cairo operating system libraries available to your
app.

If you see errors during ``briefcase build`` of the form::

    Could not find dependency: libSomething.so.1

but the app works under ``briefcase dev``, the problem may be an incomplete
``system_requires`` definition. The ``briefcase build`` process generates
a new environment that is completely isolated from your development
environment, so if your app has any operating system dependencies, they
*must* be listed in your ``system_requires`` definition.

``linuxdeploy_plugins``
~~~~~~~~~~~~~~~~~~~~~~~

A list of `linuxdeploy plugins
<https://docs.appimage.org/packaging-guide/from-source/linuxdeploy-user-guide.html#plugin-system>`__
that you wish to be included when building the AppImage. This is needed for
applications that depend on libraries that have dependencies that cannot be
automatically discovered by Linuxdeploy. GTK and Qt both have complex
runtime resource requirements that can be difficult for Linuxdeploy to
identify automatically.

The ``linuxdeploy_plugins`` declaration is a list of strings. Briefcase can take
plugin definitions in three formats:

1. The name of a plugin known by Briefcase. One of ``gtk`` or ``qt``.
2. A URL where a plugin can be downloaded
3. A path to a local plugin file

If your plugin requires an environment variable for configuration, that
environment variable can be provided as a prefix to the plugin declaration,
similar to how environment variables can be defined for a shell command.

For example, the ``gtk`` plugin requires the ``DEPLOY_GTK_VERSION`` environment
variable. To set this variable with the Briefcase-managed GTK Linuxdeploy plugin,
you would define::

    linuxdeploy_plugins = ["DEPLOY_GTK_VERSION=3 gtk"]

Or, if you were using a plugin stored as a local file::

    linuxdeploy_plugins = ["DEPLOY_GTK_VERSION=3 path/to/plugins/linuxdeploy-gtk-plugin.sh"]

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

Platform quirks
===============

Use caution with ``--update-support``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Care should be taken when using the ``--update-support`` option to the
``update``, ``build`` or ``run`` commands. Support packages in Linux AppImages
are overlaid with app content, so it isn't possible to remove all old support
files before installing new ones.

Briefcase will unpack the new support package without cleaning up existing
support package content. This *should* work; however, ensure a reproducible
release artefacts, it is advisable to perform a clean app build before release.

Apps using WebKit2 are not supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

WebKit2, the library that provides web widget support, can't currently be deployed with
AppImage. WebKit2 uses subprocesses to manage network and rendering requests, but the
way it packages and launches these subprocesses isn't currently compatible with
AppImage.

In addition, many of the commonly used ``manylinux`` base images predate the release of
WebKit2. As a result, system packages providing WebKit2 are not available on these base
images. ``manylinux_2_28`` is the earliest supported ``manylinux`` image that provides
WebKit2 support.

Runtime issues with AppImages
=============================

Packaging on Linux is a difficult problem - especially when it comes to binary
libraries. The following are some common problems you may see, and ways that
they can be mitigated.

Missing ``libcrypt.so.1``
~~~~~~~~~~~~~~~~~~~~~~~~~

The support package used by Briefcase has a `number of runtime requirements
<https://gregoryszorc.com/docs/python-build-standalone/main/running.html#runtime-requirements>`__.
One of those requirements is ``libcrypt.so.1``, which *should* be provided by
most modern Linux distributions, as it is mandated as part of the Linux Standard
Base Core Specification. However, some Red Hat maintained distributions don't
include ``libcrypt.so.1`` as part of the base OS configuration. This can usually
be fixed by installing the ``libxcrypt-compat`` package.

Failure to load ``libpango-1.0-so.0``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Older Linux distributions (e.g., Ubuntu 18.04) may not be compatible with
AppImages of Toga apps produced by Briefcase, complaining about problems with
``libpango-1.0.so.0`` and an undefined symbols
(``fribidi_get_par_embedding_levels_ex`` is a common missing symbol to be
reported). This is caused because the version of ``fribidi`` provided by these
distributions. Unfortunately, there's no way to fix this limitation.

Undefined symbol and Namespace not available errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you get the error::

    ValueError: Namespace Something not available

or::

    ImportError: /usr/lib/libSomething.so.0: undefined symbol: some_symbol

it is likely that one or more of the libraries you are using in your app
requires a Linuxdeploy plugin. GUI libraries, or libraries that do dynamic
module loading are particularly prone to this problem.

ELF load command address/offset not properly aligned
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Briefcase uses a tool named Linuxdeploy to build AppImages. Linuxdeploy
processes all the libraries used by an app so that they can be relocated into
the final packaged binary. Building a ``manylinux`` binary wheel involves a tool
named ``auditwheel`` that performs a very similar process. Unfortunately,
processing a binary with Linuxdeploy after it has been processed by
``auditwheel`` can result in a binary library that cannot be loaded at runtime.

This is particularly common when a module installed as a binary wheel has a
dependency on external libraries. For example, Pillow is a Python library that
contains a binary submodule; that submodule uses ``libpng``, ``libtiff``, and
other system libraries for image manipulation. If you install Pillow from a
``manylinux`` wheel, you may see an error similar to the following at runtime::

    Traceback (most recent call last):
    File "/tmp/.mount_TestbewwDi98/usr/app/testbed/app.py", line 54, in main
      test()
    File "/tmp/.mount_TestbewwDi98/usr/app/testbed/linux.py", line 94, in test_pillow
       from PIL import Image
    File "/tmp/.mount_TestbewwDi98/usr/app_packages/PIL/Image.py", line 132, in <module>
       from . import _imaging as core
    ImportError: libtiff-d0580107.so.5.7.0: ELF load command address/offset not properly aligned

This indicates that one of the libraries that has been included in the AppImage
has become corrupted as a result of double processing.

The solution is to ask Briefcase to install the affected library from source.
This can be done by adding a ``"--no-binary"`` entry to the ``requires``
declaration for your app. For example, if your app includes Pillow as a
requirement::

    requires = ["pillow==9.1.0"]

You can force Briefcase to install Pillow from source by adding::

    requires = [
        "pillow==9.1.0",
        "--no-binary", "pillow",
    ]

Since the library will be installed from source, you also need to add any system
requirements that are needed to compile the binary library. For example, Pillow
requires the development libraries for the various image formats that it uses::

    system_requires = [
        ... other system requirements ...
        "libjpeg-dev",
        "libpng-dev",
        "libtiff-dev",
    ]

If you are missing a system requirement, the call to ``briefcase build`` will
fail with an error::

     error: subprocess-exited-with-error

     × pip subprocess to install build dependencies did not run successfully.
     │ exit code: 1
     ╰─> See above for output.

     note: This error originates from a subprocess, and is likely not a problem with pip.
     >>> Return code: 1

     Unable to install requirements. This may be because one of your
     requirements is invalid, or because pip was unable to connect
     to the PyPI server.

You must add a separate ``--no-binary`` option for every binary library you want
to install from source. For example, if your app also includes the
``cryptography`` library, and you want to install that library from source, you
would add::

    requires = [
        "pillow==9.1.0",
        "cryptography==37.0.2",
        "--no-binary", "pillow",
        "--no-binary", "cryptography",
    ]

If you want to force *all* packages to be installed from source, you can add a
single ``:all`` declaration::

    requires = [
        "pillow==9.1.0",
        "cryptography==37.0.2",
        "--no-binary", ":all:",
    ]

The ``--no-binary`` declaration doesn't need to be added to the same
``requires`` declaration that defines the requirement. For example, if you have
a library that is used on all platforms, the declaration will probably be in the
top-level ``requires``, not the platform-specific ``requires``. If you add
``--no-binary`` in the top-level requires, the use of a binary wheel would be
prevented on *all* platforms. To avoid this, you can add the requirement in the
top-level requires, but add the ``--no-binary`` declaration to the
Linux-specific requirements::

    [tool.briefcase.app.helloworld]
    formal_name = "Hello World"
    ...
    requires = [
        "pillow",
    ]

    [tool.briefcase.app.helloworld.linux]
    requires = [
        "--no-binary", "pillow"
    ]
