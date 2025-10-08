===================
macOS Xcode project
===================

+--------+-------+---------+--------+---+-----+--------+-----+-------+
| Host Platform Support (:ref:`platform-support-key`)                |
+--------+-------+---------+--------+---+-----+--------+-----+-------+
| macOS          | Windows              | Linux                      |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+
| x86‑64 | arm64 | x86 | x86‑64 | arm64 | x86 | x86‑64 | arm | arm64 |
+========+=======+=====+========+=======+=====+========+=====+=======+
| |f|    | |f|   |     |        |       |     |        |     |       |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+

Briefcase supports creating a full Xcode project for a macOS app. This project can then
be used to build an app bundle, with the ``briefcase build`` command or directly from
Xcode.

You can specify the use of the macOS Xcode project backend by using ``briefcase <command>
macOS Xcode``.

Most apps will have no need to use the Xcode format - the :doc:`./app` format provides
everything that is required to run most macOS apps. The Xcode project format is useful
if you need to customize the stub binary that is used to start your app.

All macOS apps, regardless of output format, use the same icon formats, have the same
set of configuration and runtime options, have the same permissions, and have the same
platform quirks. See :doc:`the documentation on macOS apps <./index>` for more
details.

Application configuration
=========================

Any configuration option specified in the ``tool.briefcase.app.<appname>.macOS`` section
of your ``pyproject.toml`` file will be used by the macOS Xcode project. To specify a
setting that will *only* be used by an Xcode project and *not* other macOS output
formats, put the setting in a ``tool.briefcase.app.<appname>.macOS.Xcode`` section of your
``pyproject.toml``.
