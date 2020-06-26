=============================
Upgrading from Briefcase v0.2
=============================

Briefcase v0.2 was built as a setuptools extension. The configuration for your
project was contained in a ``setup.py`` or ``setup.cfg`` file, and you invoked
Briefcase using ``python setup.py <platform>``.

Briefcase v0.3 represents a significant change in the development of Briefcase.
Briefcase is now a `PEP518-compliant build tool
<https://www.python.org/dev/peps/pep-0518/>`__. It uses ``pyproject.toml`` for
configuration, and is invoked using a standalone ``briefcase`` command. This
change gives significantly improved flexibility in configuring Briefcase apps,
and much better control over the development process.

However, this change is also **backwards incompatible**. If you have a project
that was using Briefcase v0.2, you'll need to make some major changes to your
configuration and processes as part of upgrading to v0.3.

Configuration
=============

To port your application's configuration to Briefcase v0.3, you'll need to add
a ``pyproject.toml`` file (in, as the extension suggests, `TOML format
<https://github.com/toml-lang/toml>`__). This file contains similar content to
your ``setup.py`` or ``setup.cfg`` file.

The following is a minimal starting point for your ``pyproject.toml`` file::

    [tool.briefcase]
    project_name = "My Project"
    bundle = "com.example"
    version = "0.1"
    author = "Jane Developer"
    author_email = "jane@example.com"
    requires = []

    [tool.briefcase.app.myapp]
    formal_name = "My App"
    description = "My first Briefcase App"
    requires = []
    sources = ['src/myapp']

    [tool.briefcase.app.myapp.macOS]
    requires = ['toga-cocoa==0.3.0.dev15']

    [tool.briefcase.app.myapp.windows]
    requires = ['toga-winforms==0.3.0.dev15']

    [tool.briefcase.app.myapp.linux]
    requires = ['toga-gtk==0.3.0.dev15']

    [tool.briefcase.app.myapp.iOS]
    requires = ['toga-iOS==0.3.0.dev15']

The configuration sections are tool specific, and start with the prefix
``tool.briefcase``. Additional dotted paths define the specificity of the
settings that follow.

Most of the keys in your ``setup.py`` will map directly to
the same key in your ``pyproject.toml`` (e.g., ``version``, ``description``).
However, the following pointers may help port other values.

* Briefcase v0.2 assumed that a ``setup.py`` file described a single app.
  Briefcase v0.3 allows a project to define multiple distributable
  applications. The ``project_name`` is the name for the collection of apps
  described by this ``pyproject.toml``; ``formal_name`` is the name for a
  single app. If your project defines a single app, your formal name and
  project name will probably be the same.

* There is no explicit definition for the app's ``name`` - the app name is
  derived from the section header name (i.e., ``[tool.briefcase.app.myapp]``
  defines the existence of an app named ``myapp``).

* ``version`` *must* be defined as a string in your ``pyproject.toml`` file.
  If you need to know the version of your app (or the value of any other app
  metadata specified in ``pyproject.toml``) at runtime, you should use
  `importlib.metadata
  <https://docs.python.org/3/library/importlib.metadata.html>`__. Briefcase
  will create ``myapp.dist-info`` for your application (using your app name
  instead of ``myapp``).

* Briefcase v0.3 configuration files are heirarchical. ``[tool.briefcase]``
  describes configuration arguments for the entire project;
  ``[tool.briefcase.app.myapp]`` describes configuration arguments for the
  application named ``myapp``; ``[tool.briefcase.app.myapp.macOS]`` describes
  configuration arguments for macOS deployments of ``myapp``, and
  ``[tool.briefcase.app.myapp.macOS.dmg]`` describes configuration arguments
  for DMG deployments of ``myapp`` on macOS. The example above doesn't contain
  a ``dmg`` section; generally, you won't need one unless you're packaging
  for multiple output formats on a single platform.

  For most keys, the "most specific" value wins - so, a value for
  ``description`` defined at the platform level will override any value at the
  app level, and so on. The two exceptions are ``requires`` and ``sources``,
  which are cumulative - the values defined at the platform level will be *appended*
  to the values at the app level and the project level.

* The ``install_requires`` and ``app_requires`` keys in ``setup.py`` are
  replaced by ``requires`` in your ``pyproject.toml``. ``requires`` can be
  specified at the project level, the app level, the platform level, or the
  output format level.

* The ``packages`` (and other various source code and data-defining attributes)
  in ``setup.py`` have been replaced with a single ``sources`` key. The
  paths specified in sources will be copied in their entirety into the packaged
  application.

Once you've created and tested your ``pyproject.toml``, you can delete your
``setup.py`` file. You may also be able to delete your ``setup.cfg`` file,
depending on whether it defines any tool configurations (e.g., ``flake8`` or
``pytest`` configurations).

Invocation
==========

In Briefcase v0.2, there was only one entry point: ``python setup.py
<platform>``. This would generate a complete output artefact; and, if you
provided the ``-s`` argument, would also start the app.

Briecase v0.3 uses it's own ``briefcase`` entry point, with :doc:`subcommands
</reference/commands/index>` to perform specific functions:

 * ``briefcase new`` - Bootstrap a new project (generating a ``pyproject.toml``
   and other stub content).

 * ``briefcase dev`` - Run the app in developer mode, using the current
   virtual environment.

 * ``briefcase create`` - Use the platform template to generate the files
   needed to build a distributable artefact for the platform.

 * ``briefcase update`` - Update the source code of the application in the
   generated project.

 * ``briefcase build`` - Run whatever compilation process is necessary to
   produce an executable file for the platform.

 * ``briefcase run`` - Run the executable file for the platform.

 * ``briefcase package`` - Perform whatever post-processing is necessary to
   wrap the executable into a distributable artefact (e.g., an installer).

When using these commands, there is no need to specify the platform (i.e.
``macOS`` when on a Mac). The current platform will be detected and the
appropriate output format will be selected.

If you want to target a different platform, you can specify that platform as an
argument. This will be required when building for mobile platforms (since
you'll never be running Briefcase where the mobile platform is "native"). For
example, if you're on a Mac, ``briefcase create macOS`` and ``briefcase
create`` would perform the same task; ``briefcase create iOS`` would build an
iOS project.

The exceptions to this platform specification are ``briefcase new`` and
``briefcase dev``. These two commands are platform agnostic.

The Briefcase subcommands will also detect if previous steps haven't been
executed, and invoke any prior steps that are required. For example, if you
execute ``briefcase run`` on clean project, Briefcase will detect that there
are no platform files, and will automatically run ``briefcase create`` and
``briefcase build``. This won't occur on subsequent runs.

Briefcase v0.3 also allows for multiple output formats on a single platform.
The only platform that currently exposes capability is macOS, which supports
both ``app`` and ``dmg`` output formats (with ``dmg`` being the platform
default).

To use a different output format, add the format as an extra argument to each
command after the platform. For example, to create a ``app`` file for macOS,
you would run::

    $ briefcase create macOS app
    $ briefcase build macOS app
    $ briefcase run macOS app
    $ briefcase package macOS app

In the future, we hope to add other output formats for other platforms - `Snap
<https://snapcraft.io/>`__ and `FlatPak <https://flatpak.org/>`__ on Linux;
`NSIS <https://nsis.sourceforge.io/>`__ installers on Windows, and possibly
others. If you're interested in adding support for one of these platforms,
please `get in touch <https://gitter.im/beeware/general>`__ (or, submit a
pull request!)
