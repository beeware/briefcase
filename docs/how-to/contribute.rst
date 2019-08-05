Contributing to Briefcase
=========================


If you experience problems with Briefcase, `log them on GitHub`_. If you want to contribute code, please `fork the code`_ and `submit a pull request`_.

.. _log them on Github: https://github.com/beeware/briefcase/issues
.. _fork the code: https://github.com/beeware/briefcase
.. _submit a pull request: https://github.com/beeware/briefcase/pulls


Setting up your development environment
---------------------------------------

The recommended way of setting up your development environment for Briefcase is
to install a `virtual environment
<https://docs.python.org/3/library/venv.html>`, install the required
dependencies and start coding. Assuming that you are using
``virtualenvwrapper``, you only have to run::

    $ git clone https://github.com/beeware/briefcase.git
    $ cd briefcase
    $ python3 -m venv venv
    $ . venv/bin/activate  # For Windows CMD: venv\Scripts\activate

Briefcase uses ``unittest`` (or ``unittest2`` for Python < 2.7) for its own test
suite as well as additional helper modules for testing. To install all the
requirements for Briefcase, you have to run the following commands within your
virtual environment::

    $ (venv) pip install -e .  # for Windows CMD: pip install -e cd

Now you are ready to start hacking! Have fun!
