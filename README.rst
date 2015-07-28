Briefcase
=========

Tools to support converting a Python project into a standalone native
application.

Quickstart
----------

In your virtualenv, install Briefcase::

    $ pip install briefcase

Then, add extra options to your ``setup.py`` file to provide the
app-specific properties of your app. Settings that are applicable
to any app can be set under the ``app`` key; platform
specific settings can be specified using a platform key::

    setup(
        ...
        options={
            'app': {
                'formal_name': 'My First App',
                'bundle': 'org.example',
            },
            'osx': {
                'app_requires': [
                    'toga[osx]'
                ]
            },
            'ios': {
                'app_requires': [
                    'toga[ios]'
                ]
            },
            'android': {
                'app_requires': [
                    'toga[android]'
                ]
            },
        }
    )

At a minimum, you must set a ``formal_name`` key (the full, formal name for the
app) and a ``bundle`` key (the bundle identifier for the author organization -
usually a reverse domain name).

Then, you can invoke ``briefcase``, using::

    $ python setup.py osx

to create an OS/X app, or::

    $ python setup.py ios

to create an iOS app, or::

    $ python setup.py android

to create an Android app.

.. Documentation
.. -------------

.. Documentation for Briefcase can be found on `Read The Docs`_.

Community
---------

Briefcase is part of the `BeeWare suite`_. You can talk to the community through:

 * `@pybeeware on Twitter`_

 * The `BeeWare Users Mailing list`_, for questions about how to use the BeeWare suite.

 * The `BeeWare Developers Mailing list`_, for discussing the development of new features in the BeeWare suite, and ideas for new tools for the suite.

Contributing
------------

If you experience problems with Briefcase, `log them on GitHub`_. If you
want to contribute code, please `fork the code`_ and `submit a pull request`_.

.. _BeeWare suite: http://pybee.org
.. _Read The Docs: http://briefcase.readthedocs.org
.. _@pybeeware on Twitter: https://twitter.com/pybeeware
.. _BeeWare Users Mailing list: https://groups.google.com/forum/#!forum/beeware-users
.. _BeeWare Developers Mailing list: https://groups.google.com/forum/#!forum/beeware-developers
.. _log them on Github: https://github.com/pybee/briefcase/issues
.. _fork the code: https://github.com/pybee/briefcase
.. _submit a pull request: https://github.com/pybee/briefcase/pulls
