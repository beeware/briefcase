Contributing code to Briefcase
==============================

If you experience problems with Briefcase, `log them on GitHub`_. If you want
to contribute code, please `fork the code`_ and `submit a pull request`_.

.. _log them on Github: https://github.com/beeware/briefcase/issues
.. _fork the code: https://github.com/beeware/briefcase
.. _submit a pull request: https://github.com/beeware/briefcase/pulls

.. _setup-dev-environment:

Setting up your development environment
---------------------------------------

The recommended way of setting up your development environment for Briefcase is
to use a `virtual environment <https://docs.python.org/3/library/venv.html>`__,
and then install the development version of Briefcase and its dependencies:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      $ git clone https://github.com/beeware/briefcase.git
      $ cd briefcase
      $ python3 -m venv venv
      $ . venv/bin/activate
      (venv) $ python3 -m pip install -Ue ".[dev]"

  .. group-tab:: Linux

    .. code-block:: bash

      $ git clone https://github.com/beeware/briefcase.git
      $ cd briefcase
      $ python3 -m venv venv
      $ . venv/bin/activate
      (venv) $ python3 -m pip install -Ue ".[dev]"

  .. group-tab:: Windows

    .. code-block:: doscon

      C:\...>git clone https://github.com/beeware/briefcase.git
      C:\...>cd briefcase
      C:\...>py -m venv venv
      C:\...>venv\Scripts\activate
      (venv) C:\...>python3 -m pip install -Ue .[dev]

Briefcase uses a tool called `Pre-Commit <https://pre-commit.com>`__ to identify
simple issues and standardize code formatting. It does this by installing a git
hook that automatically runs a series of code linters prior to finalizing any
git commit. To enable pre-commit, run:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      (venv) $ pre-commit install
      pre-commit installed at .git/hooks/pre-commit

  .. group-tab:: Linux

    .. code-block:: bash

      (venv) $ pre-commit install
      pre-commit installed at .git/hooks/pre-commit

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>pre-commit install
      pre-commit installed at .git/hooks/pre-commit

When you commit any change, pre-commit will run automatically. If there are any
issues found with the commit, this will cause your commit to fail. Where possible,
pre-commit will make the changes needed to correct the problems it has found:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      (venv) $ git add some/interesting_file.py
      (venv) $ git commit -m "Minor change"
      black....................................................................Failed
      - hook id: black
      - files were modified by this hook

      reformatted some/interesting_file.py

      All done! ✨ 🍰 ✨
      1 file reformatted.

      flake8...................................................................Passed
      check toml...........................................(no files to check)Skipped
      check yaml...........................................(no files to check)Skipped
      check for case conflicts.................................................Passed
      check docstring is first.................................................Passed
      fix end of files.........................................................Passed
      trim trailing whitespace.................................................Passed
      isort....................................................................Passed
      pyupgrade................................................................Passed
      docformatter.............................................................Passed

  .. group-tab:: Linux

    .. code-block:: bash

      (venv) $ git add some/interesting_file.py
      (venv) $ git commit -m "Minor change"
      black....................................................................Failed
      - hook id: black
      - files were modified by this hook

      reformatted some/interesting_file.py

      All done! ✨ 🍰 ✨
      1 file reformatted.

      flake8...................................................................Passed
      check toml...........................................(no files to check)Skipped
      check yaml...........................................(no files to check)Skipped
      check for case conflicts.................................................Passed
      check docstring is first.................................................Passed
      fix end of files.........................................................Passed
      trim trailing whitespace.................................................Passed
      isort....................................................................Passed
      pyupgrade................................................................Passed
      docformatter.............................................................Passed

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>git add some/interesting_file.py
      (venv) C:\...>git commit -m "Minor change"
      black....................................................................Failed
      - hook id: black
      - files were modified by this hook

      reformatted some\interesting_file.py

      All done! ✨ 🍰 ✨
      1 file reformatted.

      flake8...................................................................Passed
      check toml...........................................(no files to check)Skipped
      check yaml...........................................(no files to check)Skipped
      check for case conflicts.................................................Passed
      check docstring is first.................................................Passed
      fix end of files.........................................................Passed
      trim trailing whitespace.................................................Passed
      isort....................................................................Passed
      pyupgrade................................................................Passed
      docformatter.............................................................Passed

You can then re-add any files that were modified as a result of the pre-commit checks,
and re-commit the change.

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      (venv) $ git add some/interesting_file.py
      (venv) $ git commit -m "Minor change"
      black....................................................................Passed
      flake8...................................................................Passed
      check toml...........................................(no files to check)Skipped
      check yaml...........................................(no files to check)Skipped
      check for case conflicts.................................................Passed
      check docstring is first.................................................Passed
      fix end of files.........................................................Passed
      trim trailing whitespace.................................................Passed
      isort....................................................................Passed
      pyupgrade................................................................Passed
      docformatter.............................................................Passed
      [bugfix e3e0f73] Minor change
      1 file changed, 4 insertions(+), 2 deletions(-)

  .. group-tab:: Linux

    .. code-block:: bash

      (venv) $ git add some/interesting_file.py
      (venv) $ git commit -m "Minor change"
      black....................................................................Passed
      flake8...................................................................Passed
      check toml...........................................(no files to check)Skipped
      check yaml...........................................(no files to check)Skipped
      check for case conflicts.................................................Passed
      check docstring is first.................................................Passed
      fix end of files.........................................................Passed
      trim trailing whitespace.................................................Passed
      isort....................................................................Passed
      pyupgrade................................................................Passed
      docformatter.............................................................Passed
      [bugfix e3e0f73] Minor change
      1 file changed, 4 insertions(+), 2 deletions(-)

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>git add some\interesting_file.py
      (venv) C:\...>git commit -m "Minor change"
      black....................................................................Passed
      flake8...................................................................Passed
      check toml...........................................(no files to check)Skipped
      check yaml...........................................(no files to check)Skipped
      check for case conflicts.................................................Passed
      check docstring is first.................................................Passed
      fix end of files.........................................................Passed
      trim trailing whitespace.................................................Passed
      isort....................................................................Passed
      pyupgrade................................................................Passed
      docformatter.............................................................Passed

Briefcase uses `PyTest <https://pytest.org>`__ for its own test suite. It uses
`tox <https://tox.readthedocs.io/en/latest/>`__ to manage the testing process.
To set up a testing environment and run the full test suite:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      (venv) $ tox

  .. group-tab:: Linux

    .. code-block:: bash

      (venv) $ tox

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox

By default this will run the test suite multiple times, once on each Python
version supported by Briefcase, as well as running some pre-commit checks of
code style and validity. This can take a while, so if you want to speed up
the process while developing, you can run the tests on one Python version only:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      (venv) $ tox -e py

  .. group-tab:: Linux

    .. code-block:: bash

      (venv) $ tox -e py

  .. group-tab:: Windows

    .. code-block:: bash

      (venv) C:\...>tox -e py

Or, to run using a specific version of Python, e.g. when you want to use Python 3.7:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      (venv) $ tox -e py37

  .. group-tab:: Linux

    .. code-block:: bash

      (venv) $ tox -e py37

  .. group-tab:: Windows

    .. code-block:: bash

      (venv) C:\...>tox -e py37

substituting the version number that you want to target. You can also specify
the `towncrier-check`, `docs` or `package` targets to check release notes,
documentation syntax and packaging metadata, respectively.

Add change information for release notes
----------------------------------------

Briefcase uses `towncrier <https://pypi.org/project/towncrier/>`__ to automate
building release notes. To support this, every pull request needs to have a
corresponding file in the ``changes/`` directory that provides a short
description of the change implemented by the pull request.

This description should be a high level summary of the change from the
perspective of the user, not a deep technical description or implementation
detail. It should also be written in past tense (i.e., "Added an option to
enable X" or "Fixed handling of Y").

See `News Fragments <https://pypi.org/project/towncrier/#news-fragments>`__
for more details on the types of news fragments you can add. You can also see
existing examples of news fragments in the ``changes/`` folder.

Now you are ready to start hacking! Have fun!
