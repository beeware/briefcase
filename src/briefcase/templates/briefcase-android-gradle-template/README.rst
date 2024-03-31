Briefcase Android Gradle Template
=================================

A `Cookiecutter <https://github.com/cookiecutter/cookiecutter/>`__ template for
building Python apps that will run under Android.

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

    $ cookiecutter https://github.com/beeware/briefcase-android-gradle-template

   This will ask you for a number of details of your application, including the
   `name` of your application (which should be a valid PyPI identifier), and
   the `Formal Name` of your application (the full name you use to describe
   your app). The remainder of these instructions will assume a `name` of
   ``my-project``, and a formal name of ``My Project``.

3. Add your code to the template, into the ``My Project/app/src/main/python``
   directory. At the very minimum, you need to have an ``<app
   name>/__main__.py`` file that invokes
   ``org.beeware.android.MainActivity.setPythonApp()``, providing an
   ``IPythonApp`` instance. This provides the hooks into the Android application
   lifecycle (``onCreate``, ``onResume`` and so on); it's up to you what your
   code does with those lifecycle hooks.

   If your code has any dependencies, they should be listed in the file
   ``My Project/app/requirements.txt``.

If you've done this correctly, a project with a formal name of ``My Project``,
with an app name of ``my-project`` should have a directory structure that
looks something like::

    My Project/
        app/
            src/
                main/
                    python/
                        my_project/
                            __init__.py
                            __main__.py (declares IPythonApp)
                cpp/
                    ...
                java/
                    ...
                res/
                    ...
                AndroidManifest.xml
            build.gradle
            proguard-rules.pro
            requirements.txt
        briefcase.toml
        build.gradle
        gradle.properties
        gradlew
        gradlew.bat
        settings.gradle

You're now ready to build and run your project! Either open the ``My Project``
directory in Android Studio, or `use the command line tools
<https://developer.android.com/studio/build/building-cmdline>`__.

Next steps
----------

Of course, running Python code isn't very interesting by itself - you'll be
able to output to the console, and see that output in the Logcat, but if you tap the
app icon on your phone, you won't see anything - because there isn't a visible
console on an Android.

To do something interesting, you'll need to work with the native Android system
libraries to draw widgets and respond to screen taps. The `Chaquopy`_ Java
bridging library can be used to interface with the Android system libraries.

Alternatively, you could use a cross-platform widget toolkit that supports
Android (such as `Toga`_) to provide a GUI for your application. Toga
automatically handles creating the ``IPythonApp`` instance and responding to the
app's lifecycle hooks.

.. _cookiecutter: https://github.com/cookiecutter/cookiecutter
.. _Chaquopy: https://chaquo.com/chaquopy/
.. _Toga: https://beeware.org/project/projects/libraries/toga
