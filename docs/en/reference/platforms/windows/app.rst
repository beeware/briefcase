==================
Windows App folder
==================

+--------+-------+---------+--------+---+-----+--------+-----+-------+
| Host Platform Support (:ref:`platform-support-key`)                |
+--------+-------+---------+--------+---+-----+--------+-----+-------+
| macOS          | Windows              | Linux                      |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+
| x86‑64 | arm64 | x86 | x86‑64 | arm64 | x86 | x86‑64 | arm | arm64 |
+========+=======+=====+========+=======+=====+========+=====+=======+
|        |       |     | |f|    |       |     |        |     |       |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+

A Windows App folder is a stub binary, along with a collection of subfolders that
contain the Python code for the app and the Python runtime libraries.

A Windows App folder is the default Briefcase output format when running on Windows.
However, you can explicitly specify the use of the Windows App folder backend by using
``briefcase <command> windows app``.

All Windows apps, regardless of output format, use the same icon formats, have the same
set of configuration and runtime options, have the same permissions, and have the same
platform quirks. See :doc:`the documentation on Windows apps <./index>` for
more details.

Application configuration
=========================

Any configuration option specified in the ``tool.briefcase.app.<appname>.windows``
section of your ``pyproject.toml`` file will be used by the Windows App folder backend.
To specify a setting that will *only* be used by Windows App folders and *not* other
Windows output formats, put the setting in a
``tool.briefcase.app.<appname>.windows.app`` section of your ``pyproject.toml``.
