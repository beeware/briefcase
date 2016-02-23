Contributing to Briefcase
=========================


If you experience problems with Briefcase, `log them on GitHub`_. If you want to contribute code, please `fork the code`_ and `submit a pull request`_.

.. _log them on Github: https://github.com/pybee/briefcase/issues
.. _fork the code: https://github.com/pybee/briefcase
.. _submit a pull request: https://github.com/pybee/briefcase/pulls


Setting up your development environment
---------------------------------------

The recommended way of setting up your development envrionment for Briefcase
is to install a virtual environment, install the required dependencies and
start coding. Assuming that you are using ``virtualenvwrapper``, you only have
to run::

    $ git clone git@github.com:pybee/briefcase.git
    $ cd briefcase
    $ mkvirtualenv briefcase

Briefcase uses ``unittest`` (or ``unittest2`` for Python < 2.7) for its own test
suite as well as additional helper modules for testing. To install all the
requirements for Briefcase, you have to run the following commands within your
virutal envrionment::

    $ pip install -e .

Now you are ready to start hacking! Have fun!
