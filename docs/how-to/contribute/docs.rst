Contributing to the documentation
=================================

Here are some tips for working on this documentation. You're welcome to add
more and help us out!

First of all, you should check the `reStructuredText (reST) Primer
<https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_ to learn how
to write your .rst file.

Create a .rst file
---------------------

Look at the structure and choose the best category to put your .rst file. Make
sure that it is referenced in the index of the corresponding category, so it
will show on in the documentation. If you have no idea how to do this, study
the other index files for clues.

Build documentation locally
---------------------------

.. Docs are always built on Python 3.12. See also the RTD and tox config.

To build the documentation locally, :ref:`set up a development environment
<setup-dev-environment>`. However, you **must** have a Python 3.12 interpreter installed
and available on your path (i.e., ``python3.12`` must start a Python 3.12 interpreter).

You'll also need to install the Enchant spell checking library.

.. tabs::

  .. group-tab:: macOS

    Enchant can be installed using `Homebrew <https://brew.sh>`__:

    .. code-block:: console

      (venv) $ brew install enchant

    If you're on an Apple Silicon machine, you'll also need to manually set the location
    of the Enchant library:

    .. code-block:: console

      (venv) $ export PYENCHANT_LIBRARY_PATH=/opt/homebrew/lib/libenchant-2.2.dylib

  .. group-tab:: Linux

    Enchant can be installed as a system package:

    **Ubuntu 20.04+ / Debian 10+**

    .. code-block:: console

      $ sudo apt-get update
      $ sudo apt-get install enchant-2

    **Fedora**

    .. code-block:: console

      $ sudo dnf install enchant

    **Arch, Manjaro**

    .. code-block:: console

      $ sudo pacman -Syu enchant

  .. group-tab:: Windows

    Enchant is installed automatically when you set up your development
    environment.

Once your development environment is set up, run:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox -e docs

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox -e docs

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox -e docs

The output of the file should be in the ``docs/_build/html`` folder. If there
are any markup problems, they'll raise an error.

Live documentation preview
--------------------------

To support rapid editing of documentation, Briefcase also has a "live preview" mode:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox -e docs-live

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox -e docs-live

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox -e docs-live

This will build the documentation, start a web server to serve the build documentation,
and watch the file system for any changes to the documentation source. If a change is
detected, the documentation will be rebuilt, and any browser viewing the modified page
will be automatically refreshed.

Documentation linting
---------------------

Before committing and pushing documentation updates, run linting for the
documentation:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox -e docs-lint

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox -e docs-lint

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox -e docs-lint

This will validate the documentation does not contain:

* invalid syntax and markup
* dead hyperlinks
* misspelled words

If a valid spelling of a word is identified as misspelled, then add the word to
the list in ``docs/spelling_wordlist``. This will add the word to the
spellchecker's dictionary.

Rebuilding all documentation
----------------------------

To force a rebuild for all of the documentation:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox -e docs-all

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox -e docs-all

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox -e docs-all

The documentation should be fully rebuilt in the ``docs/_build/html`` folder.
If there are any markup problems, they'll raise an error.
