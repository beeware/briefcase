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

Clone Briefcase and create virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      $ git clone https://github.com/beeware/briefcase.git
      $ cd briefcase
      $ python3 -m venv venv
      $ . venv/bin/activate
      (venv) $ python3 -m pip install -Ue ".[dev]"

  .. group-tab:: Linux

    .. code-block:: console

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

Install pre-commit
^^^^^^^^^^^^^^^^^^

Briefcase uses a tool called `pre-commit <https://pre-commit.com>`__ to identify
simple issues and standardize code formatting. It does this by installing a git
hook that automatically runs a series of code linters prior to finalizing any
git commit. To enable pre-commit, run:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ pre-commit install
      pre-commit installed at .git/hooks/pre-commit

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ pre-commit install
      pre-commit installed at .git/hooks/pre-commit

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>pre-commit install
      pre-commit installed at .git/hooks/pre-commit

Pre-commit automatically runs during the commit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With pre-commit installed as a git hook for verifying commits, the pre-commit
hooks configured in ``.pre-commit-config.yaml`` for Briefcase must all pass
before the commit is successful. If there are any issues found with the commit,
this will cause your commit to fail. Where possible, pre-commit will make the
changes needed to correct the problems it has found:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ git add some/interesting_file.py
      (venv) $ git commit -m "Minor change"
      check toml...........................................(no files to check)Skipped
      check yaml...........................................(no files to check)Skipped
      check for case conflicts.................................................Passed
      check docstring is first.................................................Passed
      fix end of files.........................................................Passed
      trim trailing whitespace.................................................Passed
      isort....................................................................Passed
      pyupgrade................................................................Passed
      docformatter.............................................................Passed
      black....................................................................Failed
      - hook id: black
      - files were modified by this hook

      reformatted some/interesting_file.py

      All done! ✨ 🍰 ✨
      1 file reformatted.

      flake8...................................................................Passed


  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ git add some/interesting_file.py
      (venv) $ git commit -m "Minor change"
      check toml...........................................(no files to check)Skipped
      check yaml...........................................(no files to check)Skipped
      check for case conflicts.................................................Passed
      check docstring is first.................................................Passed
      fix end of files.........................................................Passed
      trim trailing whitespace.................................................Passed
      isort....................................................................Passed
      pyupgrade................................................................Passed
      docformatter.............................................................Passed
      black....................................................................Failed
      - hook id: black
      - files were modified by this hook

      reformatted some/interesting_file.py

      All done! ✨ 🍰 ✨
      1 file reformatted.

      flake8...................................................................Passed

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>git add some/interesting_file.py
      (venv) C:\...>git commit -m "Minor change"
      check toml...........................................(no files to check)Skipped
      check yaml...........................................(no files to check)Skipped
      check for case conflicts.................................................Passed
      check docstring is first.................................................Passed
      fix end of files.........................................................Passed
      trim trailing whitespace.................................................Passed
      isort....................................................................Passed
      pyupgrade................................................................Passed
      docformatter.............................................................Passed
      black....................................................................Failed
      - hook id: black
      - files were modified by this hook

      reformatted some/interesting_file.py

      All done! ✨ 🍰 ✨
      1 file reformatted.

      flake8...................................................................Passed

You can then re-add any files that were modified as a result of the pre-commit checks,
and re-commit the change.

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ git add some/interesting_file.py
      (venv) $ git commit -m "Minor change"
      check toml...........................................(no files to check)Skipped
      check yaml...........................................(no files to check)Skipped
      check for case conflicts.................................................Passed
      check docstring is first.................................................Passed
      fix end of files.........................................................Passed
      trim trailing whitespace.................................................Passed
      isort....................................................................Passed
      pyupgrade................................................................Passed
      docformatter.............................................................Passed
      black....................................................................Passed
      flake8...................................................................Passed
      [bugfix daedd37a] Minor change
       1 file changed, 2 insertions(+)
       create mode 100644 some/interesting_file.py

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ git add some/interesting_file.py
      (venv) $ git commit -m "Minor change"
      check toml...........................................(no files to check)Skipped
      check yaml...........................................(no files to check)Skipped
      check for case conflicts.................................................Passed
      check docstring is first.................................................Passed
      fix end of files.........................................................Passed
      trim trailing whitespace.................................................Passed
      isort....................................................................Passed
      pyupgrade................................................................Passed
      docformatter.............................................................Passed
      black....................................................................Passed
      flake8...................................................................Passed
      [bugfix daedd37a] Minor change
       1 file changed, 2 insertions(+)
       create mode 100644 some/interesting_file.py

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>git add some\interesting_file.py
      (venv) C:\...>git commit -m "Minor change"
      check toml...........................................(no files to check)Skipped
      check yaml...........................................(no files to check)Skipped
      check for case conflicts.................................................Passed
      check docstring is first.................................................Passed
      fix end of files.........................................................Passed
      trim trailing whitespace.................................................Passed
      isort....................................................................Passed
      pyupgrade................................................................Passed
      docformatter.............................................................Passed
      black....................................................................Passed
      flake8...................................................................Passed
      [bugfix daedd37a] Minor change
       1 file changed, 2 insertions(+)
       create mode 100644 some/interesting_file.py

Running tests and coverage
--------------------------

Briefcase uses `tox <https://tox.wiki/en/latest/>`__ to manage the testing
process and `pytest <https://docs.pytest.org/en/latest>`__ for its own test
suite.

The default ``tox`` command includes running:
 * pre-commit hooks
 * towncrier release note check
 * documentation linting
 * test suite for available Python versions
 * code coverage reporting

.. note::

    The argument of ``p`` for the ``tox`` command is short-hand for
    ``run-parallel``. As that implies, tox runs the checks concurrently and
    only shows the output/errors from checks that fail.

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox p

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox p

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox p

Run tests for multiple versions of Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, many of the ``tox`` commands will attempt to run the test suite
multiple times, once for each Python version supported by Briefcase. To do
this, though, each of the Python versions must be installed on your machine
and available to tox's Python `discovery
<https://virtualenv.pypa.io/en/latest/user_guide.html#python-discovery>`__
process. In general, if a version of Python is available via ``PATH``, then
tox should be able to find and use it.

Run only the test suite
^^^^^^^^^^^^^^^^^^^^^^^

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox -e py

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox -e py

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox -e py

Run the test suite for specific files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox -e py -- tests/path/to/test_some_test.py

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox -e py -- tests/path/to/test_some_test.py

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox -e py -- tests/path/to/test_some_test.py

Run the test suite for a specific Python version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox -e py310

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox -e py310

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox -e py310

Run the test suite without coverage (fast)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This will run the test suite in multiple processes and can be dramatically
faster. This mode does not produce coverage files due to complexities in
capturing coverage within spawned processes.

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox -e py-fast

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox -e py-fast

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox -e py-fast

Understanding conditional coverage
----------------------------------

Briefcase maintains 100% branch coverage in its codebase. When you add or
modify code in the project, you must add test code to ensure coverage of any
changes you make.

Given, though, that Briefcase targets macOS, Linux, and Windows, as well as
multiple versions of Python, full coverage cannot be verified on a single
platform. To accommodate this, several conditional coverage rules are defined
in ``pyproject.toml``, such as ``no-cover-if-is-windows``, and used in the
project to identify sections of code that are only covered on particular
platforms.

Coverage report for host platform and Python version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After running the test suite, you can generate a coverage report that ignores
missing coverage for code for other platforms or version of Python by running:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox -e coverage

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox -e coverage

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox -e coverage

To run the test suite along with this coverage reporting, run:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox p -m test

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox p -m test

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox p -m test

Coverage report for host platform
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If all supported versions of Python are available to tox, then coverage for the
host platform can be reported by running:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox -e coverage-platform

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox -e coverage-platform

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox -e coverage-platform

To run the test suite along with this coverage reporting, run:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox p -m test-platform

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox p -m test-platform

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox p -m test-platform

Coverage reporting in HTML
^^^^^^^^^^^^^^^^^^^^^^^^^^

Additionally, an HTML coverage report can be generated by appending ``-html``
to any of the coverage tox environment names, for instance:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox -e coverage-platform-html

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox -e coverage-platform-html

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox -e coverage-platform-html

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

See `News Fragments
<https://towncrier.readthedocs.io/en/stable/tutorial.html#creating-news-fragments>`__
for more details on the types of news fragments you can add. You can also see
existing examples of news fragments in the ``changes/`` folder.

Simulating GitHub CI checks locally
-----------------------------------

To run the same checks that run in CI for the platform, run:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ tox p -m ci

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ tox p -m ci

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>tox p -m ci

Now you are ready to start hacking! Have fun!
