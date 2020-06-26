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
support library. This support library was compiled on Ubuntu 16.04, which means
the AppImages build by Briefcase can be used on *any* Linux distribution of
about the same age or newer - but those AppImages *must* be compiled on Ubuntu
16.04.

This means you have four options for using Briefcase to compile a Linux
AppImage:

1. Run the version-sensitive parts of the build process inside Docker. This is
   the default behavior of Briefcase. This also means that it is possible to
   build Linux binaries on any platform that can run Docker.

2. Install Ubuntu 16.04 on your own machine.

3. Find a cloud or CI provider that can provide you an Ubuntu 16.04
   machine for build purposes. Github Actions, for example, provides Ubuntu
   16.04 as a build option. Again, you'll need to use the ``--no-docker``
   command line option.

4. Build your own version of the BeeWare `Python support libraries
   <https://github.com/beeware/Python-Linux-support>`__. If you take this
   approach, be aware that your AppImage will only be as portable as the
   version of libc that is available on the distribution you use. If you build
   using Ubuntu 19.10, for example, you can expect that only people on the most
   recent versions of another distribution will be able to run your AppImage.

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
entries should be Ubuntu 16.04 `apt` package requirements.
