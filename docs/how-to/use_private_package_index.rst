Using a private package index
=============================


If your project depends on packages not available on pipy, e.g. if you use briefcase in a corporate environment and
you're unfortunately not allowed to open source your packages, you need to set up a private package index and configure
`pip` to use it to enable briefcase to find your packages.

The fastest way to get a local index up and running is to use _pypiserver.

.. _pypiserver pipyserver: https://pypi.org/project/pypiserver/


1. Install a local pypiserver
-----------------------------
In case you're already running your own index, skip this step.::

    $ pip install pipyserver passlib
    $ htpasswd -sc htpasswd.txt my_user
    $ mkdir packages
    $ pypi-server -p 8080 -P htpasswd.txt packages


2. Configure pip, distutils and twine
-------------------------------------

~/.pip/pip.conf ::

    [global]
    extra-index-url = http://localhost:8080/simple/



~/.pypirc ::

    [distutils]
    index-servers =
      pypi
      local

    [pypi]
    username:<your_pypi_username>
    password:<your_pypi_passwd>

    [local]
    repository: http://localhost:8080
    username: my_user
    password: my_password


3. Push your sdist
------------------

Using setuptools (legacy)
^^^^^^^^^^^^^^^^^^^^^^^^^

Now you should be able to push an sdist to your local index using::

    $ python setup.py sdist upload -r local


This way of publishing packages is deprecated, but still works with `pypi-server`.

Using twine (recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^

When you push the package for the first time, you need to register it:::

    twine register -r local dist/*.tar.gz

now you're able to upload it:::

    twine upload -r local dist/*



4. Configure briefcase to use your package
------------------------------------------

After adding your dependency to your setup.py you're now able to finally build your briefcase app. ::

    ...
    'macos': {
        'app_requires': [
            'toga-cocoa==0.3.0.dev11',
            'your-private-package'
        ]
    },
    ...


