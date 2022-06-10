==============
Linux AppImage
==============

`AppImage <https://appimage.org>`__ provides a way for developers to provide
"native" binaries for Linux users. It allow packaging applications for any
common Linux based operating system, including Ubuntu, Debian, Fedora, and
more. AppImages contain all the dependencies that cannot be assumed to
be part of each target system, and will run on most Linux distributions
without further modifications.

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

Binary Dependencies in apps
---------------------------

Packaging for AppImage has one special constraint - you **cannot** use
``manylinux`` binary wheels. Building an AppImage involves using a tool named
``linuxdeploy``; ``linuxdeploy`` processes all the libraries used by an app so
that they can be relocated into the final packaged binary. Building a
``manylinux`` binary wheel involves a tool called ``auditwheel`` that performs a
very similar process. Unfortunately, the two tools are mutually incompatible.
Once a binary has been processed by ``auditwheel``, it strips some of the
information needed for ``linuxdeploy`` to operate successfully.

As a result, **all** binary dependencies referenced by your application **must
be installed from source**. For example, if you use Pillow for image processing,
you **cannot** use the binary ``manylinux`` wheels that are available on PyPI -
you need to use the source distribution, and compile the extension at time of
install.

Briefcase will prevent you from installing binary wheels; however, this means
you need to ensure that any libraries or development tools needed to compile
your binary dependencies are present in your build environment. This means
either using the ``system_requires`` option for Docker-based builds; or
installing those packages into your development environment for non-Docker
builds. For example, to compile Pillow, you need to add ``libjpeg-dev``,
``libpng-dev`` and ``libtiff-dev`` to your ``system_requires`` (or the
equivalent packages in for your development environment).

Icon format
===========

AppImages use ``.png`` format icons.

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
entries should be Ubuntu 18.04 ``apt`` package requirements. For example::

    system_requires = ['libgirepository1.0-dev', 'libcairo2-dev']

would make the GTK GI and Cairo operating system libraries available to your
app.

If you see errors during ``briefcase build`` of the form::

    Could not find dependency: libSomething.so.1

or you have errors about compiling wheels for packages, like::

    error: subprocess-exited-with-error

    × pip subprocess to install build dependencies did not run successfully.
    │ exit code: 1
    ╰─> See above for output.

    note: This error originates from a subprocess, and is likely not a problem with pip.
    >>> Return code: 1

    Unable to install dependencies. This may be because one of your
    dependencies is invalid, or because pip was unable to connect
    to the PyPI server.

but the app works under ``briefcase dev``, the problem may be an incomplete
``system_requires`` definition. The ``briefcase build`` process generates
a new environment that is completely isolated from your development
environment, so if your app has any operating system dependencies, they
*must* be listed in your ``system_requires`` definition.
