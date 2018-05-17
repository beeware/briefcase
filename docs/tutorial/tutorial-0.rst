Tutorial 0 - Hello, world!
==========================

In this tutorial, you'll take a really simple "Hello, world!" program written
in Python, convert it into a working project.

Setup
-----

This tutorial assumes you've read and followed the instructions in
:doc:`/background/getting-started`. If you've done this, you should have:

* A ``tutorial`` directory,
* A activated Python 3.5 virtual environment,
* Briefcase installed in that virtual environment,
* Any platform-specific dependencies installed.

Start a new project
-------------------

Let's get started by using
`the handy template <https://github.com/pybee/briefcase-template>`_
``briefcase-template``:

.. code-block:: bash

    $ pip install cookiecutter briefcase
    $ cookiecutter https://github.com/pybee/briefcase-template

This will ask a bunch of questions of you. We'll use an `app_name` of
"helloworld", a `formal_name` of "Hello World", using the Toga GUI toolkit.
You can use the default values for the other questions (or update them
to reflect your own name if you want).

You'll now have a few files in this folder, including a ``helloworld``
directory.

Check out what the provided ``helloworld/app.py`` file contains:

.. code-block:: bash

    $ cd helloworld
    $ cat helloworld/app.py

.. code-block:: python

    
    import toga
    from toga.style import Pack
    from toga.style.pack import COLUMN, ROW


    class HelloWorld(toga.App):
        def startup(self):
            # Create a main window with a name matching the app
            self.main_window = toga.MainWindow(title=self.name)

            # Create a main content box
            main_box = toga.Box()

            # Add the content on the main window
            self.main_window.content = main_box

            # Show the main window
            self.main_window.show()


    def main():
        return HelloWorld('Hello World', 'com.example.helloworld')

Put it in a briefcase
---------------------

Your project is now ready to use ``briefcase``.

Windows
~~~~~~~

To create and run the application, run:

.. code-block:: bash

    $ python setup.py windows -s

This will produce a ``windows`` subdirectory that will contain a
``HelloWorld-0.0.1.msi`` installer. If you get an error stating that 
Wix Tools cannot be found, and you have already installed them, try restarting 
your computer.

macOS
~~~~~

To create and run the application, run:

.. code-block:: bash

    $ python setup.py macos -s

This will produce a ``macOS`` subdirectory that contains a ``Hello World.app``
application bundle. This bundle can be dragged into your Applications folder,
or zipped and distributed to anyone else.

Linux
~~~~~

To create and run the application, run:

.. code-block:: bash

    $ python setup.py linux -s

This will produce a ``linux`` subdirectory that contains a ``Hello World``
script that will start the application.

iOS
~~~

To create and run the application, run:

.. code-block:: bash

    $ python setup.py ios -s

This will start the iOS simulator (you may be asked to select an API and a
simulator device on which to run the app) and run your app.

It will also produce an ``ios`` subdirectory that contains an XCode project
called ``Hello World.xcodeproj``. You can open this project in XCode to run
your application.

Android
~~~~~~~

To create and run the application, run:

.. code-block:: bash

    $ python setup.py android -s

This will produce an ``android`` subdirectory that contains a Gradle project.
It will also launch the app on the first Android device or simulator that
can be found running on (or attached to) your computer.

What should happen
------------------

When the application runs, you should see a window with a title of "Hello
World" appear. The window won't contain any content - but it will be a native
application, with a native icon in your task bar (or wherever icons appear on
your platform).

You've just packaged your first app with Briefcase! Now, let's :doc:`make the
app actually do something interesting </tutorial/tutorial-1>`.
