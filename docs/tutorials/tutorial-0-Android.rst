Android Tutorial 0 - Hello, world!
===================================

In this tutorial, you'll take a really simple "Hello, world!" program written in
Python, convert it into a native Android project.

Setup
-----

This tutorial assumes you've read and followed the instructions in
:doc:`/intro/getting-started`. This Tutorial is for Android Developers and Users!

* A ``tutorial`` directory,
* An activated Python 3 virtual environment
* Briefcase installed in that virtual environment
* We need gradle installed https://gradle.org/
* The Android SDK and installation guid can be found at https://developer.android.com/studio/index.html
* Ensure that the path to Android sdk is found.
* THATS IT YOU ARE READY TO GO!


Start a new project Using the Beeware Tool Kit
---------------------------------------------------

Let's get started by using `the handy template <https://github.com/pybee/briefcase-template>`_ ``briefcase-template``:

.. code-block:: bash

    $ pip install cookiecutter briefcase
    $ cookiecutter https://github.com/pybee/briefcase-template

This will ask a bunch of questions of you. We'll use an `app_name` of "tutorial_0", and a 
`formal_name` of "Tutorial 0". Set the other values as you like.You'll now have a few files in this folder, including ``tutorial_0``. 

Check out what the provided ``tutorial_0/app.py`` file contains:

.. code-block:: bash

    (BeeWare)user$ cd tutorial_0
    (BeeWare)user$ cat tutorial_0/app.py

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

Create an Android project from the existing code
-----------------------------------------------------
It is all ready for using ``briefcase``. You can invoke it, using:


.. code-block:: bash

    $ python setup.py android


    
Lets now convert your app to an apk with ./gradlew
--------------------------------------------------

There is a new folder in the project called 'android'.  
From within the android folder with the virtual environment still activated you
will run: 

.. code-block:: bash

    ./gradlew build

Now its time to see what we have created.  Plug in your android phone(or
emulated Android phone) and make sure you are still in the virtual environment
we created at the start.  If you are then run:


.. code-block:: bash

  (Beeware)$ ./gradlew run


....Poof.... your android apk is in the
/android/build/outputs/apk/android-release-unsigned.apk.  You will
still need to sign the apk, but you should see the phone running your android
application!
   
And that is all, you created your first Android python app!
Beeware is amazing right?
