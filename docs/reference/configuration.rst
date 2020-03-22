=====================
Configuration options
=====================

Briefcase is a `PEP518 <https://www.python.org/dev/peps/pep-0518/>`__-compliant
build tool. It uses a ``pyproject.toml`` file, in the root directory of your
project, to provide build instructions for the packaged file.

If you have an application called "My App", with source code in the `src/myapp`
directory, the simplest possible ``pyproject.toml`` Briefcase configuration
file would be::

    [build-system]
    requires = ["briefcase"]

    [tool.briefcase]
    project_name = "My Project"
    bundle = "com.example"
    version = "0.1"

    [tool.briefcase.app.myapp]
    formal_name = "My App"
    description = "My first Briefcase App"
    sources = ['src/myapp']

The ``[build-system]`` section is preamble required by PEP518, declaring the
dependency on Briefcase.

The remaining sections are tool specific, and start with the prefix
``tool.briefcase``.

The location of the ``pyproject.toml`` file is treated as the root of the
project definition. Briefcase should be invoked in a directory that contains a
``pyproject.toml`` file, and all relative file path references contained in the
``pyproject.toml`` file will be interpreted relative to the directory that
contains the ``pyproject.toml`` file.

Configuration sections
======================

A project that is packaged by Briefcase can declare multiple *applications*.
Each application is a distributable product of the build process. A simple
project will only have a single application. However, a complex project may
contain multiple applications with shared code.

Each setting can be specified:

* At the level of an output format (e.g., settings specific to building macOS
  DMGs);
* At the level of an platform for an app (e.g., macOS specific settings);
* At the level of an individual app; or
* Globally, for all applications in the project.

When building an application in a particular output format, Briefcase will look
for settings in the same order. For example, if you're building a macOS DMG for
an application called ``myapp``, Briefcase will look for macOS DMG settings for
``myapp``, then for macOS settings for ``myapp``, then for ``myapp`` settings,
then for project-level settings.

``[tool.briefcase]``
--------------------

The base `[tool.briefcase]` section declares settings that project specific,
or are are common to all applications in this repository.

``[tool.briefcase.app.<app name>]``
-----------------------------------

Configuration options for a specific application.

``<app name>`` must adhere to a valid Python distribution name as
specified in `PEP508 <https://www.python.org/dev/peps/pep-0508/#names>`__.

``[tool.briefcase.app.<app name>.<platform>]``
----------------------------------------------

Configuration options for an application that are platform specific. The
platform must match a name for a platform supported by Briefcase (e.g.,
``macOS`` or ``windows``). A list of the platforms supported by Briefcase can
be obtained by running ``briefcase -h``, and inspecting the help for the
``platform`` option

``[tool.briefcase.app.<app name>.<platform>.<output format>]``
--------------------------------------------------------------

Configuration options that are specific to a particular output format. For
example, ``macOS`` applications can be generated in ``app`` or ``dmg`` format.

Project configuration
=====================

Required values
---------------

``bundle``
~~~~~~~~~~

A reverse-domain name that can be used to identify resources for the
application e.g., ``com.example``. The bundle identifier will be combined with
the app name to produce a unique application identifier - e.g., if the bundle
identifier is ``com.example`` and the app name is ``myapp`, the application
will be identified as ``com.example.myapp``.

``project_name``
~~~~~~~~~~~~~~~~

The project is the collection of all applications that are described by the
briefcase configuration. For projects with a single app, this may be the same
as the formal name of the solitary packaged app.

``version``
~~~~~~~~~~~

A `PEP440 <https://www.python.org/dev/peps/pep-0440/>`__ compliant version
string.

Examples of valid version strings:

* ``1.0``
* ``1.2.3``
* ``1.2.3.dev4`` - A development release
* ``1.2.3a5`` - An alpha pre-release
* ``1.2.3b6`` - A Beta pre-release
* ``1.2.3rc7`` - A release candidate
* ``1.2.3.post8`` - A post-release

Optional values
---------------

``author``
~~~~~~~~~~

The person or organization responsible for the project.

``author_email``
~~~~~~~~~~~~~~~~

The contact email address for the person or organization responsible for the
project.

``url``
~~~~~~~

A URL where more details about the project can be found.

Application configuration
=========================

Required
--------

``description``
~~~~~~~~~~~~~~~

A short, one-line description of the purpose of the application.

``sources``
~~~~~~~~~~~

A list of paths, relative to the pyproject.toml file, where source code for the
application can be found. The contents of any named files or folders will be
copied into the application bundle. Parent directories in any named path will
not be included. For example, if you specify ``src/myapp`` as a source, the
contents of the `myapp` folder will be copied into the application bundle; the
src directory will not be reproduced.

Unlike most other keys in a configuration file, ``sources`` is *cumlative*
setting. If an application defines sources at the global level, application
level, *and* platform level, the final set of sources will be the
*concatenation* of sources from all levels, starting from least to most
specific.

Optional values
---------------

``author``
~~~~~~~~~~

The person or organization responsible for the application.

``author_email``
~~~~~~~~~~~~~~~~

The contact email address for the person or organization responsible for the
application.

``formal_name``
~~~~~~~~~~~~~~~

The application name as it should be displayed to humans. This name may contain
capitalization and punctuation. If it is not specified, the ``name`` will be
used.

``icon``
~~~~~~~~

A path, relative to the directory where the ``pyproject.toml`` file is located,
to an image to use as the icon for the application. The path should *exclude*
the extension; Briefcase will append a platform appropriate extension when
configuring the application. For example, an icon specification of ``icon =
"resources/icon"`` will use ``resources/icon.icns`` on macOS, and
``resources/icon.ico`` on Windows.

Some platforms require multiple icons, at different sizes; these will be
handled by appending the required size to the provided icon name. For example,
iOS requires multiple icon sizes (ranging from 20px to 1024px); Briefcase will
look for ``resources/icon-20.png``, ``resources/icon-1024.png``, and so on. The
sizes that are required are determined by the platform template.

``installer_icon``
~~~~~~~~~~~~~~~~~~

A path, relative to the directory where the ``pyproject.toml`` file is located,
to an image to use as the icon for the installer. As with ``icon``, the
path should *exclude* the extension, and a platform-appropriate extension will
be appended when the application is built.

``installer_background``
~~~~~~~~~~~~~~~~~~~~~~~~

A path, relative to the directory where the ``pyproject.toml`` file is located,
to an image to use as the background for the installer. As with ``splash``, the
path should *exclude* the extension, and a platform-appropriate extension will
be appended when the application is built.

``requires``
~~~~~~~~~~~~

A list of packages that must be packaged with this application.

Unlike most other keys in a configuration file, ``requires`` is *cumlative*
setting. If an application defines requirements at the global level,
application level, *and* platform level, the final set of requirements will be
the *concatenation* of requirements from all levels, starting from least to
most specific.

``splash``
~~~~~~~~~~

A path, relative to the directory where the ``pyproject.toml`` file is located,
to an image to use as the splash screen for the application. The path should
*exclude* the extension; Briefcase will append a platform appropriate extension
when configuring the application.

Some platforms require multiple splash images, at different sizes; these will
be handled by appending the required size to the provided icon name. For
example, iOS requires multiple splash screens, (including 1024x768px,
768x1024px, 2048x1536px, and more); Briefcase will look for
``resources/splash-1024x768.png``, ``resources/splash-768x1024.png``,
``resources/splash-2048x1536.png``, and so on. The sizes that are required are
determined by the platform template.

Some platforms also require different *variants* (e.g., both portrait and
landscape splash screens). These variants can be specified by qualifying the
splash specification:

    splash.portrait = "resource/portrait-splash"
    splash.landscape = "resource/landscape-splash"

If the platform output format does not use a splash screen, the ``splash``
setting is ignored. If the platform requires both variants *and* sizes, the
handling will be combined.

``support_package``
~~~~~~~~~~~~~~~~~~~

A file path or URL pointing at a tarball containing a Python support package.
(i.e., a precompiled, embeddable Python interpreter for the platform)

If this setting is not provided, Briefcase will use the default support
package for the platform.

``support_revision``
~~~~~~~~~~~~~~~~~~~~

The specific revision of a support package that should be used. By default,
Briefcase will always use the most recently released support package; if you
specify a support revision, the support package will be pinned to that version
for your app.

If the support package is a URL, a query argument of
``revision=<support_revision>`` will be added to the support package URL when
it is downloaded.

If the support package is a file path, this argument is ignored.

``template``
~~~~~~~~~~~~

A file path or URL pointing at a `cookiecutter
<https://github.com/cookiecutter/cookiecutter>`__ template for the output
format.

If this setting is not provided, Briefcase will use a default template for
the output format and Python version.

``url``
~~~~~~~

A URL where more details about the application can be found.

Document types
==============

Applications in a project can register themselves with the operating system as
handlers for specific document types by adding a ``document_type``
configuration section for each document type the application can support. This
section follows the format:

    ``[tool.briefcase.app.<app name>.document_type.<extension>]``

or, for a platform specific definition:

    ``[tool.briefcase.app.<app name>.<platform>.document_type.<extension>]``

where ``extension`` is the file extension to register. For example, ``myapp``
could register as a handler for PNG image files by defining the configuration
section ``[tool.briefcase.app.myapp.document_type.png]``.

The document type declaration requires the following settings:

``description``
---------------

A short, one-line description of the document format.

``icon``
--------

A path, relative to the directory where the ``pyproject.toml`` file is located,
to an image for an icon to register for use with documents of this type. The
path should *exclude* the extension; Briefcase will append a platform
appropriate extension when configuring the applcation. For example, an icon
specification of::

    icon = "resources/icon"

will use ``resources/icon.icns`` on macOS, and ``resources/icon.ico`` on
Windows.

Some platforms also require different *variants* (e.g., both square and round
icons). These variants can be specified by qualifying the icon specification:

    icon.round = "resource/round-icon"
    icon.square = "resource/square-icon"

Some platforms require multiple icons, at different sizes; these will be
handled by appending the required size to the provided icon name. For example,
iOS requires multiple icon sizes (ranging from 20px to 1024px); Briefcase will
look for ``resources/icon-20.png``, ``resources/icon-1024.png``, and so on. The
sizes that are required are determined by the platform template.

If a platform requires both different sizes *and* variants, the variant
handling and size handling will be combined. For example, Android requires
round and square icons, in sizes ranging from 48px to 192px; Briefcase will
look for ``resource/round-icon-42.png``, ``resource/square-icon-42.png``,
``resource/round-icon-192.png``, and so on.

``url``
-------

A URL for help related to the document format.
