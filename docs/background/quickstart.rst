Quickstart
==========

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
            'macos': {
                'app_requires': [
                    'toga-cocoa'
                ],
                'icon': 'icons/macos',
            },
            'ios': {
                'app_requires': [
                    'toga-ios'
                ],
                'icon': 'images/ios_icon',
                'splash': 'images/ios_splash',
            },
            'android': {
                'app_requires': [
                    'toga-android'
                ],
                'icon': 'images/android_icon',
                'splash': 'images/android_splash',
            },
            'tvos': {
                'app_requires': [
                    'toga-ios'
                ]
            },
            'django': {
                'app_requires': [
                    'toga-django'
                ]
            },
        }
    )

At a minimum, you must set a ``formal_name`` key (the full, formal name for the
app) and a ``bundle`` key (the bundle identifier for the author organization -
usually a reverse domain name).

Alternatively, if you're starting from scratch, you can use `cookiecutter`_ to
generate a stub project with the required content::

    $ pip install cookiecutter
    $ cookiecutter https://github.com/pybee/briefcase-template

.. _cookiecutter: http://github.com/audreyr/cookiecutter

Then, you can invoke ``briefcase``, using:

* macOS: ``$ python setup.py macos``
* Windows: ``$ python setup.py windows``
* Linux: ``$ python setup.py linux``
* iOS: ``$ python setup.py ios``
* Android: ``$ python setup.py android``
* tvOS: ``$ python setup.py tvos``


You can also use the ``-b`` (or ``--build``) argument to automatically
perform any compilation step required; or use ``-s`` (``--start``) to
start the application.

For desktop OS's (macOS, Windows, Linux) the entry point(s) to your program can
be defined in ``setup.py`` as console and gui scripts::

    setup(
        ...
        entry_points={
            'gui_scripts': [
                'Example = example.gui:main [GUI]',
            ],
            'console_scripts': [
                'utility = example.main:main',
            ]
        }
        ...

For more details on the format see:
http://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins

On Windows and Linux this allows for multiple executables to be defined.
macOS will use the entry point with the same name as your `formal_name` as the
main application, any others will be available in the Contents/MacOS folder inside the
application bundle.

For other platforms the entry point is defined in the platform template, typically
they require the __main__.py module to be defined explicitly in code.
