=====================
Visual Studio project
=====================

+--------+-------+---------+--------+---+-----+--------+-----+-------+
| Host Platform Support (:ref:`platform-support-key`)                |
+--------+-------+---------+--------+---+-----+--------+-----+-------+
| macOS          | Windows              | Linux                      |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+
| x86‑64 | arm64 | x86 | x86‑64 | arm64 | x86 | x86‑64 | arm | arm64 |
+========+=======+=====+========+=======+=====+========+=====+=======+
|        |       |     | |f|    |       |     |        |     |       |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+

Briefcase supports creating a full Visual Studio project for a Windows app. This
project can then be used to build the stub app binary with the ``briefcase
build`` command, or directly from Visual Studio.

You can specify the use of the Windows Visual Studio project backend by using
``briefcase <command> windows visualstudio``.

Most apps will have no need to use the Visual Studio project format - the :doc:`./app`
format provides everything that is required to run most Windows apps. The Visual Studio
project format is useful if you need to customize the stub binary that is used to start
your app.

All Windows apps, regardless of output format, use the same icon formats, have the same
set of configuration and runtime options, have the same permissions, and have the same
platform quirks. See :doc:`the documentation on Windows apps <./index>` for more
details.

Pre-requisites
==============

Building the Visual Studio project requires that you install Visual Studio 2022
or later. Visual Studio 2022 Community Edition `can be downloaded for free from
Microsoft <https://visualstudio.microsoft.com/vs/community/>`__. You can also
use the Professional or Enterprise versions if you have them.

Briefcase will auto-detect the location of your Visual Studio installation,
provided one of the following three things are true:

1. You install Visual Studio in the standard location in your Program Files folder.
2. ``MSBuild.exe`` is on your path.
3. You define the environment variable ``MSBUILD`` that points at the location of
   your ``MSBuild.exe`` executable.

When you install Visual Studio, there are many optional components. You should
ensure that you have installed the following:

* .NET Desktop Development
  - All default packages
* Desktop Development with C++
  - All default packages
  - C++/CLI support for v143 build tools

Application configuration
=========================

Any configuration option specified in the ``tool.briefcase.app.<appname>.windows``
section of your ``pyproject.toml`` file will be used by the Windows Visual Studio
project. To specify a setting that will *only* be used by a Visual Studio project and
*not* other Windows output formats, put the setting in a
``tool.briefcase.app.<appname>.windows.visualstudio`` section of your
``pyproject.toml``.
