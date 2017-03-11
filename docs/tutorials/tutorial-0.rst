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

Lets start by creating a ``iostutorial`` directory:

.. code-block:: bash

    $ mkdir iostutorial
    $ cd iostutorial

Now, we create our simple "Hello, world!" application:

.. code-block:: bash

    $ mkdir HelloWorld
    $ touch HelloWorld/__init__.py
    $ echo 'print("Hello, World!")' > HelloWorld/app.py

.. note:: In ``ios`` the application entry point is always ``ApplicationName/app.py``

Finally, we have to add the setuptools ``setup.py`` script:

.. code-block:: python

    #!/usr/bin/env python
    
    from setuptools import setup, find_packages
    
    setup(name='HelloWorld',
        version = '0.1',
        packages = find_packages(),
        options = {
            'app': {
                'formal_name': 'Hello World',
                'bundle': 'org.example'
            },
            'ios': {
                'app_requires': [
                ]
            }
        }
    )

In the setup script we included the basic information of our application (``name``, ``version`` and ``packages``) needed by setuptools for deploying our application. Additionally, we added in the ``options`` the required configuration for ``briefcase``. 

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

    open iOS/Hello\ World.xcodeproj

You can test the app by running it in Xcode. As our application only shows a message, the iOS application will show only a blank screen. You can check if it is working in the console logs, which should contain something like this:

.. code-block:: bash

    Hello World.app/Library/Application Support/org.example.HelloWorld/app/HelloWorld/app.py
    Hello World!
    2016-09-16 10:49:14.564094 Hello World[6791:4292188] subsystem: com.apple.UIKit, category: HIDEventFiltered, enable_level: 0, persist_level: 0, default_ttl: 0, info_ttl: 0, debug_ttl: 0, generate_symptoms: 0, enable_oversize: 1, privacy_setting: 2, enable_private_data: 0

And that is all, you created your first iOS python app!
