======
config
======

Manage user-level defaults without editing ``pyproject.toml``. Defaults can be
stored per project (in ``.briefcase/``) or globally for your user account.

Usage
=====

Set a value (project scope):

.. code-block:: console

    $ briefcase config android.device "@Pixel_5"
    $ briefcase config iOS.device "iPhone 15"

Set a value (global scope):

.. code-block:: console

    $ briefcase config --global android.device "emulator-5554"
    $ briefcase config --global iOS.device "?"

Get a value:

.. code-block:: console

    $ briefcase config --get android.device
    $ briefcase config --global --get iOS.device

List the current file:

.. code-block:: console

    $ briefcase config --list
    $ briefcase config --global --list

Unset a value:

.. code-block:: console

    $ briefcase config --unset android.device
    $ briefcase config --global --unset iOS.device

Where settings are stored
-------------------------

- Project user config: ``<project>/.briefcase/config.toml``
- Global user config: platform user config directory, e.g.:

  - macOS: ``~/Library/Application Support/org.beeware.briefcase/config.toml``
  - Linux: ``~/.config/org.beeware.briefcase/config.toml``
  - Windows: ``%LOCALAPPDATA%\\BeeWare\\org.beeware.briefcase\\config.toml``

Format
------

On read, both a **root** TOML shape and a ``[tool.briefcase]`` block are accepted.
On write, Briefcase uses the **root** shape.

Example (project):

.. code-block:: toml

    [android]
    device = "@Pixel_5"

    [iOS]
    device = "iPhone 15"

Supported keys
--------------

- ``android.device`` — AVD name (``@Name``) or emulator id (e.g., ``emulator-5554``)
- ``iOS.device`` — UDID (``xxxxxxxx-…-xxxxxxxxxxxx``), device name (e.g., ``"iPhone 15"``),
  or ``"Device Name::iOS X[.Y]"``

Validation & special values
---------------------------

- ``?`` is allowed for both device keys to **force** interactive selection next run.
- Invalid formats are rejected with a helpful error; no file is written.

Precedence
----------

**CLI overrides > ``pyproject.toml`` > project user config > global user config**

Notes
-----

- Keys are case-sensitive (use ``iOS.device``, not ``ios.device``).
