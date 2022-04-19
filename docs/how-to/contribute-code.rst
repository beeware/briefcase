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
install the required dependencies and start coding:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      $ git clone https://github.com/beeware/briefcase.git
      $ cd briefcase
      $ python3 -m venv venv
      $ . venv/bin/activate

  .. group-tab:: Linux

    .. code-block:: bash

      $ git clone https://github.com/beeware/briefcase.git
      $ cd briefcase
      $ python3 -m venv venv
      $ . venv/bin/activate

  .. group-tab:: Windows

    .. code-block:: doscon

      C:\...>git clone https://github.com/beeware/briefcase.git
      C:\...>cd briefcase
      C:\...>py -m venv venv
      C:\...>venv\Scripts\activate

To install all the development version of Briefcase, along with all it's
requirements, run the following commands within your virtual environment:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      $ (venv) pip install -e .

  .. group-tab:: Linux

    .. code-block:: bash

      $ (venv) pip install -e .

  .. group-tab:: Windows

    .. code-block:: doscon

      C:\...>pip install -e .

Now you are ready to start hacking! Use `python3 -m briefcase` to run briefcase. Have fun!

(Optional) If you have trouble running briefcase, ensure Briefcase is in your Python path. You may add Briefcase to your Python path by using the Python shell:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      $ (venv) python3

      >>> import sys
      >>> sys.path.append("$YOUR_PATH_TO_BRIEFCASE")

  .. group-tab:: Linux

    .. code-block:: bash

      $ (venv) python3

      >>> import sys
      >>> sys.path.append("$YOUR_PATH_TO_BRIEFCASE")

  .. group-tab:: Windows

    .. code-block:: doscon

      C:\...>python3

      >>> import sys
      >>> sys.path.append("$YOUR_PATH_TO_BRIEFCASE")


Briefcase uses `PyTest <https://pytest.org>`__ for its own test suite. It uses
`tox <https://tox.readthedocs.io/en/latest/>`__ to manage the testing process.
To set up a testing environment and run the full test suite:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      $ (venv) pip install tox
      $ (venv) tox

  .. group-tab:: Linux

    .. code-block:: bash

      $ (venv) pip install tox
      $ (venv) tox

  .. group-tab:: Windows

    .. code-block:: doscon

      C:\...>pip install tox
      C:\...>tox

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

      C:\...>tox -e py

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

      C:\...>tox -e py37

substituting the version number that you want to target. You can also specify
one of the pre-commit checks `flake8`, `docs` or `package` to check code
formatting, documentation syntax and packaging metadata, respectively.

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
