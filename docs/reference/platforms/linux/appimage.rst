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

1. Install Ubuntu 16.04 on your own machine.

2. Find a cloud or CI provider that can provide you an Ubuntu 16.04
   machine for build purposes. Github Actions, for example, provides Ubuntu
   16.04 as a build option.

3. Run Briefcase inside a Docker container. Once you have `installed
   Docker <https://docs.docker.com/install/>`__, the command::

        $ docker run -it -v /path/to/project:/project ubuntu:16.04 /bin/bash

   will start a Docker container running Ubuntu 16.04, mounting your
   local project directory (``/path/to/project``) as the ``/project``
   directory in the container. You can then install the requirements
   necessary to run Briefcase inside the container::

        $ apt-get update
        $ apt-get install python3-dev
        $ pip install briefcase

   Depending on the application you're packaging, you may need to install
   additional system libraries (e.g., graphics libraries to support the GUI
   toolkit). For example, if you're intending to use BeeWare's `Toga
   <https://beeware.org/toga>`__ GUI toolkit, you'll need the following
   system libraries::

        $ apt-get install libgirepository1.0-dev libcairo2-dev libpango1.0-dev libwebkitgtk-3.0-0 gir1.2-webkit-3.0

   As an aside, using Docker will also allow you to create Linux packages on
   Windows or macOS.

4. Build your own version of the BeeWare `Python support libraries
   <https://github.com/beeware/Python-Linux-support>`__. If you take this
   approach, be aware that your AppImage will only be as portable as the
   version of libc that is available on the distribution you use. If you build
   using Ubuntu 19.10, for example, you can expect that only people on the most
   recent versions of another distribution will be able to run your AppImage.

Icon format
===========

AppImages use ``.png`` format icons.

Image format
============

AppImages do not support splash screens or installer images.
