===========
.app bundle
===========

+--------+-------+---------+--------+---+-----+--------+-----+-------+
| Host Platform Support (:ref:`platform-support-key`)                |
+--------+-------+---------+--------+---+-----+--------+-----+-------+
| macOS          | Windows              | Linux                      |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+
| x86‑64 | arm64 | x86 | x86‑64 | arm64 | x86 | x86‑64 | arm | arm64 |
+========+=======+=====+========+=======+=====+========+=====+=======+
| |f|    | |f|   |     |        |       |     |        |     |       |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+

A macOS ``.app`` bundle is a directory with a specific layout, with some key metadata.
If this structure and metadata exists, macOS treats the folder as an executable file,
giving it an icon.

An ``.app`` bundle is the default Briefcase output format when running on macOS.
However, you can explicitly specify the use of the ``.app`` bundle backend by using
``briefcase <command> macOS app``.

``.app`` bundles can be copied around as if they are a single file. They can
also be compressed to reduce their size for distribution.

All macOS apps, regardless of output format, use the same icon formats, have the same
set of configuration and runtime options, have the same permissions, and have the same
platform quirks. See :doc:`the documentation on macOS apps <./index>` for more
details.

Application configuration
=========================

Any configuration option specified in the ``tool.briefcase.app.<appname>.macOS`` section
of your ``pyproject.toml`` file will be used by the macOS ``.app`` bundle. To specify a
setting that will *only* be used by ``.app`` bundles and *not* other macOS output
formats, put the setting in a ``tool.briefcase.app.<appname>.macOS.app`` section of your
``pyproject.toml``.
