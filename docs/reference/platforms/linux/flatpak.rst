=======
Flatpak
=======

`Flatpak <https://flatpak.org>`__ provides a way for developers to distribute
apps to Linux users in a format that is independent of the specific distribution
used by the end-user. It allow packaging applications for use on any common
Linux distribution, including Ubuntu, Debian, Fedora, and more. There are some
system packages needed to run and build Flatpaks; see the `Flatpak setup guide
<https://flatpak.org/setup>`__ for more details.

A Flatpak app is built by compiling against a `runtime`. Runtimes provide the
basic dependencies that are used by applications. Each application must be built
against a runtime, and this runtime must be installed on a host system in order
for the application to run (Flatpak can automatically install the runtime
required by an application).

The end user will install the Flatpak into their local app repository; this can
be done by installing directly from a single file `.flatpak` bundle, or by
installing from a package repository like `Flathub <https://flathub.org>`__.
Apps can be installed into user-space, or if the user has sufficient privileges,
they can be installed into a system-wide app repository.

Briefcase currently supports creating `.flatpak` single file bundles; end users
can install the app bundle by running::

    $ flatpak install --user App_Name-1.2.3-x86_64.flatpak

substituting the name of the flatpak file as appropriate. The ``--user`` option
can be omitted if the user wants to install the app system-wide.

The app can then be run with::

    $ flatpak run com.example.appname

specifying the app bundle identifier as appropriate.

Briefcase *can* be published to Flathub or another Flatpak repository; but
Briefcase does not currently support automated publication of apps.

Icon format
===========

Flatpak uses ``.png`` format icons. An application must provide icons in
the following sizes:

  * 16px
  * 32px
  * 64px
  * 128px
  * 256px
  * 512px

Splash Image format
===================

Flatpaks do not support splash screens or installer images.

Application configuration
=========================

The following options can be added to the
``tool.briefcase.app.<appname>.linux`` section of your ``pyproject.toml``
file.

``flatpak_runtime_repo_alias``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An alias to use when registering the Flatpak repository that will store the
Flatpak runtime used to build the app. By default, Briefcase will use `Flathub
<flathub.org>`__ as it's runtime repository, with an alias of ``flathub``.

``flatpak_runtime_repo_url``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The repository URL hosting the runtime and SDK package that the Flatpak will
use. By default, Briefcase will use `Flathub <flathub.org>`__ as it's runtime
repository.

``flatpak_runtime``
~~~~~~~~~~~~~~~~~~~

A string, identifying the runtime to use as a base for the Flatpak app. By
default, Flatpaks build with Briefcase will use the ``org.freedesktop.Platform``
runtime.

The Flatpak runtime and SDK are paired; so if you define ``flatpak_runtime``,
you *must* also define ``flatpak_sdk``.

``flatpak_runtime_version``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A string, identifying the version of the Flatpak runtime that should be used.
Flatpaks built with Briefcase will use version ``21.08`` of the FreeDesktop
platform runtime.

``flatpak_sdk``
~~~~~~~~~~~~~~~

A string, identifying the SDK associated with the platform that will be used to
build the Flatpak app. By default, Flatpaks build with Briefcase will use the
``org.freedesktop.Sdk`` SDK. The SDK will use the same version as the runtime.

The Flatpak runtime and SDK are paired; so if you define ``flatpak_sdk``,
you *must* also define ``flatpak_runtime``.

Compilation issues with Flatpak
===============================

Flatpak works by building a sandbox in which to compile the application bundle.
This sandbox uses some low-level kernel and filesystem operations to provide the
sandboxing behavior. As a result, Flatpaks cannot be built inside a Docker
container, and they cannot be build on an NFS mounted drive.

If you get errors about ``renameat`` when building an app, similar to the
following::

    [helloworld] Building Flatpak...
    Downloading sources
    Initializing build dir
    Committing stage init to cache
    Error: Writing metadata object: renameat: Operation not permitted
    Building...

    Error while building app helloworld.

    Log saved to ...

you may be building on an NFS drive. Move your project to local storage, and
retry the build.
