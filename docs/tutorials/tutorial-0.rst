Tutorial 0 - Hello, world!
==========================

In this tutorial, you'll take a really simple "Hello, world!" program written in
Python, convert it into a working iOS project.

Setup
-----

This tutorial assumes you've read and followed the instructions in
:doc:`/intro/getting-started`. If you've done this, you should have:

* XCode installed on your Mac,
* A ``tutorial`` directory,
* A activated Python 3.4 virtual environment,
* Briefcase installed in that virtual environment,

Start a new project
-------------------

Let's get started by using `the handy template <https://github.com/pybee/briefcase-template>`_ ``briefcase-template``:

.. code-block:: bash

    $ pip install cookiecutter briefcase
    $ cookiecutter https://github.com/pybee/briefcase-template

This will ask a bunch of questions of you. We'll use an `app_name` of "tutorial_0", and a 
`formal_name` of "Tutorial 0". Set the other values as you like

You'll now have a few files in this folder, including ``tutorial_0``. 

Check out what the provided ``tutorial_0/app.py`` file contains:

.. code-block:: bash

    $ cd tutorial_0
    $ cat tutorial_0/app.py

.. code-block:: python

    def main():
        # This needs to return an object that has a main_loop() method.
        return None

This won't do much as it is, but we can make it useful. 

Add this into the ``app.py`` to make it useful:

.. code-block:: python

    class MyApp:
        def main_loop(self):
            print("Hello world")
            
            
    def main():
        return MyApp()  

Create an iOS project
---------------------

It is all ready for using ``briefcase``. You can invoke it, using:

.. code-block:: bash

    $ python setup.py ios

to create the iOS app.

Open the iOS project with Xcode
-------------------------------

There is a new folder in your project called 'iOS', which contains the Xcode project (``Hello World.xcodeproj``). Open it with Xcode and check that your application is the ``app`` folder. You can also open the application by running:

.. code-block:: bash

    open iOS/Tutorial\ 0.xcodeproj

You can test the app by running it in Xcode. As our application only shows a message, the iOS application will show only a blank screen. You can check if it is working in the console logs, which should contain something like this:

.. code-block:: bash

    Tutorial 0.app/Library/Application Support/com.pybee.tutorial0/tutorial_0/tutorial_0/app.py
    Hello World!
    2016-09-16 10:49:14.564094 Hello World[6791:4292188] subsystem: com.apple.UIKit, category: HIDEventFiltered, enable_level: 0, persist_level: 0, default_ttl: 0, info_ttl: 0, debug_ttl: 0, generate_symptoms: 0, enable_oversize: 1, privacy_setting: 2, enable_private_data: 0

And that is all, you created your first iOS python app!
