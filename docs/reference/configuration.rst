=============================
Project configuration options
=============================

Briefcase is a `PEP518 <https://www.python.org/dev/peps/pep-0518/>`__-compliant
build tool. It uses a ``pyproject.toml`` file, in the root directory of your
project, to provide build instructions for the packaged file.

If you have an application called "My App", with source code in the ``src/myapp``
directory, the simplest possible ``pyproject.toml`` Briefcase configuration
file would be::

    [tool.briefcase]
    project_name = "My Project"
    bundle = "com.example"
    version = "0.1"

    [tool.briefcase.app.myapp]
    formal_name = "My App"
    description = "My first Briefcase App"
    sources = ['src/myapp']

The configuration sections are tool specific, and start with the prefix
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

``<app name>`` must adhere to a valid Python distribution name as specified in
`PEP508 <https://www.python.org/dev/peps/pep-0508/#names>`__. The app name must
also *not* be a reserved word in Python, Java or JavaScript (i.e., app names
like ``switch`` or ``pass`` would not be valid); and it may not include any of
the `filenames prohibited by Windows
<https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file#naming-conventions>`__
(i.e., ``CON``, ``PRN``, or ``LPT1``).

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

``build``
~~~~~~~~~

A build identifier. An integer, used in addition to the version specifier,
to identify a specific compiled version of an application.

``cleanup_paths``
~~~~~~~~~~~~~~~~~

A list of strings describing paths that will be *removed* from the project after
the installation of the support package and app code. The paths provided will be
interpreted relative to the app bundle folder (e.g., the ``macOS/app/My App``
folder in the case of a macOS app).

Paths can be:
 * An explicit reference to a single file
 * An explicit reference to a single directory
 * Any filesystem glob accepted by ``pathlib.glob`` (See `the Python
   documentation for details
   <https://docs.python.org/3/library/pathlib.html#pathlib.Path.glob>`__)

Paths are treated as format strings prior to glob expansion. You can use Python
string formatting to include references to configuration properties of the app
(e.g., ``app.formal_name``, ``app.version``, etc).

For example, the following ``cleanup_paths`` specification::

    cleanup_paths = [
        "path/to/unneeded_file.txt",
        "path/to/unneeded_directory",
        "path/**/*.exe",
        "{app.formal_name}/content/extra.doc"
    ]

on an app with a formal name of "My App" would remove:

1. The file ``path/to/unneeded_file.txt``
2. The directory ``path/to/unneeded_directory``
3. Any ``.exe`` file in ``path`` or its subdirectories.
4. The file ``My App/content/extra.doc``.

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
example, iOS requires multiple splash images, (1024px, 2048px and 3072px);
with a ``splash`` setting of ``resources/my_splash``, Briefcase will look for
``resources/my_splash-1024.png``, ``resources/my_splash-2045.png``, and
``resources/my_splash-3072.png``. The sizes that are required are determined
by the platform template.

Some platforms also require different *variants*. For example, Android requires
splash screens for "normal", "large" and "xlarge" devices. These variants can
be specified by qualifying the splash specification:

    splash.normal = "resource/normal-splash"
    splash.large = "resource/large-splash"
    splash.xlarge = "resource/xlarge-splash"

These settings can, if you wish, all use the same prefix.

If the platform requires different sizes for each variant (as Android does),
those size will be appended to path provided by the variant specifier. For
example, using the previous example, Android would look for
``resource/normal-splash-320.png``,  ``resource/normal-splash-480.png``,
``resource/large-splash.480.png``, ``resource/xlarge-splash-720.png``, amongst
others.

If the platform output format does not use a splash screen, the ``splash``
setting is ignored.

``splash_background_color``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A hexidecimal RGB color value (e.g., ``#6495ED``) to use as the background
color for splash screens.

If the platform output format does not use a splash screen, this setting is
ignored.

``support_package``
~~~~~~~~~~~~~~~~~~~

A file path or URL pointing at a tarball containing a Python support package.
(i.e., a precompiled, embeddable Python interpreter for the platform)

If this setting is not provided, Briefcase will use the default support
package for the platform.

``support_revision``
~~~~~~~~~~~~~~~~~~~~

The specific revision of a support package that should be used. By default,
Briefcase will use the support package revision nominated by the application
template. If you specify a support revision, that will override the revision
nominated by the application template.

If you specify an explicit support package (either as a URL or a file path),
this argument is ignored.

``supported``
~~~~~~~~~~~~~

Indicates that the platform is not supported. For example, if you know that
the app cannot be deployed to Android for some reason, you can explicitly
prevent deployment by setting `supported=False` in the Android section of the
app configuration file.

If `supported` is set to `false`, the create command will fail, advising the
user of the limitation.

``template``
~~~~~~~~~~~~

A file path or URL pointing at a `cookiecutter
<https://github.com/cookiecutter/cookiecutter>`__ template for the output
format.

If this setting is not provided, Briefcase will use a default template for
the output format and Python version.

``template_branch``
~~~~~~~~~~~~~~~~~~~

The branch of the project template to use when generating the app. If the
template is a local file, this attribute will be ignored. If not specified,
Briefcase will use a branch matching the version of Briefcase that is being used
(i.e., if you're using Briefcase 0.3.9, Briefcase will use the `v0.3.9` template
branch when generating the app). If you're using a development version of
Briefcase, Briefcase will use the `main` branch of the template.

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
