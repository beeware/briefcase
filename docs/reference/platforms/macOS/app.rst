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
| |f|    | |y|   |     |        |       |     |        |     |       |
+--------+-------+-----+--------+-------+-----+--------+-----+-------+

A macOS ``.app`` bundle is a collection of directory with a specific layout,
and with some key metadata. If this structure and metadata exists, macOS treats
the folder as an executable file, giving it an icon.

``.app`` bundles can be copied around as if they are a single file. They can
also be compressed to reduce their size for transport.

By default, apps will be both signed and notarized when they are packaged.

Packaging format
================

Briefcase supports two packaging formats for a macOS ``.app`` bundle:

1. A DMG that contains the ``.app`` bundle (the default output of ``briefcase package
   macOS``, or by using ``briefcase package macOS -p dmg``); or
2. A zipped ``.app`` folder (using ``briefcase package macOS -p app``).

Icon format
===========

macOS ``.app`` bundles use ``.icns`` format icons.

Splash Image format
===================

macOS ``.app`` bundles do not support splash screens or installer images.

Additional options
==================

The following options can be provided at the command line when packaging
macOS apps.

``--no-notarize``
~~~~~~~~~~~~~~~~~

Do not submit the application for notarization. By default, apps will be
submitted for notarization unless they have been signed with an ad-hoc
signing identity.

Application configuration
=========================

The following options can be added to the ``tool.briefcase.app.<appname>.macOS.app``
section of your ``pyproject.toml`` file.

``universal_build``
~~~~~~~~~~~~~~~~~~~

A Boolean, indicating whether Briefcase should build a universal app (i.e, an app that
can target both x86_64 and ARM64). Defaults to ``true``; if ``false``, the binary will
only be executable on the host platform on which it was built - i.e., if you build on
an x86_64 machine, you will produce an x86_65 binary; if you build on an ARM64 machine,
you will produce an ARM64 binary.

Platform quirks
===============

Packaging with ``--adhoc-sign``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using the ``--adhoc-sign`` option on macOS produces an app that will be able
to run on your own machine, but won't run on any other computer. In order to
distribute your app to other users, you will need to sign the app with a full
signing identity.
