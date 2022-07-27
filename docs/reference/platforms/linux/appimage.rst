========
AppImage
========

`AppImage <https://appimage.org>`__ provides a way for developers to provide
"native" binaries for Linux users. It allow packaging applications for any
common Linux based operating system, including Ubuntu, Debian, Fedora, and more.
AppImages contain all the dependencies that cannot be assumed to be part of each
target system, and will run on most Linux distributions without further
modifications. Briefcase uses `linuxdeploy
<https://github.com/linuxdeploy/linuxdeploy>`__ to build the AppImage in the
correct format.

Packaging binaries for Linux is complicated, because of the inconsistent
library versions present on each distribution. An AppImage can be executed on
*any* Linux distribution with a version of ``libc`` greater than or equal the
version of the distribution where the AppImage was created.

To simplify the packaging process, Briefcase provides a pre-compiled Python
support library. This support library was compiled on Ubuntu 18.04, which means
the AppImages build by Briefcase can be used on *any* Linux distribution of
about the same age or newer - but those AppImages *must* be compiled on Ubuntu
18.04.

This means you have four options for using Briefcase to compile a Linux
AppImage:

1. Run the version-sensitive parts of the build process inside Docker. This is
   the default behavior of Briefcase. This also means that it is possible to
   build Linux binaries on any platform that can run Docker.

2. Install Ubuntu 18.04 on your own machine.

3. Find a cloud or CI provider that can provide you an Ubuntu 18.04
   machine for build purposes. Github Actions, for example, provides Ubuntu
   18.04 as a build option. Again, you'll need to use the ``--no-docker``
   command line option.

4. Build your own version of the BeeWare `Python support libraries
   <https://github.com/beeware/Python-Linux-support>`__. If you take this
   approach, be aware that your AppImage will only be as portable as the
   version of libc that is available on the distribution you use. If you build
   using Ubuntu 19.10, for example, you can expect that only people on the most
   recent versions of another distribution will be able to run your AppImage.

Icon format
===========

AppImages uses ``.png`` format icons. An application must provide icons in
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
``tool.briefcase.app.<appname>.linux`` section of your ``pyproject.toml``
file.

``system_requires``
~~~~~~~~~~~~~~~~~~~

A list of operating system packages that must be installed for the AppImage
build to succeed. If a Docker build is requested, this list will be passed to
the Docker context when building the container for the app build. By default,
entries should be Ubuntu 18.04 ``apt`` package requirements. For example,

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
automatically discovered by linuxdeploy. GTK and Qt both have complex
runtime resource requirements that can be difficult for linuxdeploy to
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
variable. To set this variable with the Briefcase-managed GTK linuxdeploy plugin,
you would define::

    linuxdeploy_plugins = ["DEPLOY_GTK_VERSION=3 gtk"]

Or, if you were using a plugin stored as a local file::

    linuxdeploy_plugins = ["DEPLOY_GTK_VERSION=3 path/to/plugins/linuxdeploy-gtk-plugin.sh"]

Runtime issues with AppImages
=============================

Packaging on Linux is a difficult problem - especially when it comes to binary
libraries. The following are some common problems you may see, and ways that
they can be mitigated.

Undefined symbol and Namespace not available errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you get the error::

    ValueError: Namespace Something not available

or::

    ImportError: /usr/lib/libSomething.so.0: undefined symbol: some_symbol

it is likely that one or more of the libraries you are using in your app
requires a linuxdeploy plugin. GUI libraries, or libraries that do dynamic
module loading are particularly prone to this problem.

ELF load command address/offset not properly aligned
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Briefcase uses a tool named ``linuxdeploy`` to build AppImages. ``linuxdeploy``
processes all the libraries used by an app so that they can be relocated into
the final packaged binary. Building a ``manylinux`` binary wheel involves a tool
named ``auditwheel`` that performs a very similar process. Unfortunately,
processing a binary with ``linuxdeploy`` after it has been processed by
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

     Unable to install dependencies. This may be because one of your
     dependencies is invalid, or because pip was unable to connect
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
linux-specific requirements::

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
