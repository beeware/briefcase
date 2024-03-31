Briefcase Linux System App Template
===================================

A `Cookiecutter <https://github.com/cookiecutter/cookiecutter/>`__ template for
building Python apps that will run under Linux, packaged as native system
packages.

Using this template
-------------------

The easiest way to use this project is to not use it at all - at least, not
directly. `Briefcase <https://github.com/beeware/briefcase/>`__ is a tool that
uses this template, rolling it out using data extracted from a
``pyproject.toml`` configuration file.

However, if you *do* want use this template directly...

1. Install `cookiecutter`_. This is a tool used to bootstrap complex project
   templates::

    $ pip install cookiecutter

2. Run ``cookiecutter`` on the template::

    $ cookiecutter https://github.com/beeware/briefcase-linux-system-template

   This will ask you for a number of details of your application, including the
   `name` of your application (which should be a valid PyPI identifier), and
   the `Formal Name` of your application (the full name you use to describe
   your app). The remainder of these instructions will assume a `name` of
   ``my-project``, and a formal name of ``My Project``.

3. Add your code to the template, into the ``My
   Project/project/usr/local/share/my_project`` directory. At
   the very minimum, you need to have an ``app/<app name>/__main__.py`` file
   that defines an entry point that will start your application.

   If your code has any dependencies, they should be installed into the
   ``My
   Project/project/usr/local/lib/my_project/app_packages`` directory.

If you've done this correctly, a project with a formal name of ``My Project``,
with an app name of ``my-project`` should have a directory structure that
looks something like::

    My Project/
        bootstrap/
            main.c
            Makefile
        project/
            usr/
                lib/
                    my-project/
                        app/
                            my_project/
                                __init__.py
                                __main__.py
                                app.py
                        app_packages/
                            ...
                share/
                    applications/
                        com.example.my-project.desktop
                    icons/
                        ...
        Dockerfile
        briefcase.toml

4. Compile and install the bootstrap binary::

    $ cd "My Project"
    $ make -C bootstrap install

6. Build the DEB package::

    $ dpkg-deb --build --root-owner-group project

This will project a ``project.deb`` file that you can install with::

    $ sudo apt install -f project.deb

Next steps
----------

Of course, running Python code isn't very interesting by itself.

To do something interesting, you'll need to work with the native system
libraries to draw widgets and respond to user input. The `GTK+`_ GUI library
provides Python bindings that you can use to build a user interface.
Alternatively, you could use a cross-platform widget toolkit that supports
Windows (such as `Toga`_) to provide a GUI for your application.

If you have any external library dependencies (like Toga, or anything other
third-party library), you should install the library code into the
``app_packages`` directory. This directory is the same as a  ``site_packages``
directory on a desktop Python install.

.. _cookiecutter: https://github.com/cookiecutter/cookiecutter
.. _Obtain a Python Linux support package for x86_64: https://github.com/beeware/Python-Linux-support
.. _Toga: https://beeware.org/project/projects/libraries/toga
.. _GTK+: https://python-gtk-3-tutorial.readthedocs.io/
