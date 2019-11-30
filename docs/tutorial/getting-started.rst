Getting Started
===============

In this guide we will walk you through setting up your Briefcase environment
for development and testing. We will assume that you have a working Python 3.5
(or later) install. If you don't have Python 3 set up yet, this `guide
<https://docs.python.org/3/using/index.html>`__ will help you get started.

Install platform dependencies
-----------------------------

Next, you'll need to make sure you've got the platform-specific dependencies
for the platforms you're going to target.

.. tabs::

  .. group-tab:: macOS

     There are no additional dependencies required to support OSX.

     If you want to build iOS, tvOS, or watchOS applications, you'll need to
     install XCode from the macOS App Store.

     Once you've installed XCode, you must also install the Xcode Command
     Line Tools. This can be done from the Preference panel within XCode
     itself.

     You'll need to sign in to XCode with your Apple ID account - the same one
     you'd use for iTunes. You can create a free personal team by clicking on
     ``Preferences > Accounts`` and adding your Apple ID account.

  .. group-tab:: Windows

    * If you're using Windows 10, you may need to enable the .NET 3.5 framework
      on your machine. Open the Control Panel, select "Programs and Features",
      then "Turn Windows features on or off". Ensure ".NET Framework 3.5
      (Includes .NET 2.0 and 3.0)" is enabled.

    * Install the `WiX toolset <https://wixtoolset.org>`__.

    * Install Git, and ensure it is included in the system PATH:
      `Git For Windows <https://git-scm.com/download/win>`__.

  .. group-tab:: Linux

    To be confirmed...

  .. group-tab:: Android

    * Install `Android Studio <https://developer.android.com/studio/index.html>`__.
      When you start Android Studio for the first time, you'll be provided a wizard
      to configure your installation; select a "standard" installation.

    * Put the ``sdk/tools``, ``sdk/platform-tools`` and ``sdk/tools/bin`` directories in your path.

      - On macOS: ``~/Library/Android/sdk/tools``, ``~/Library/Android/sdk/platform-tools`` and ``~/Library/Android/sdk/tools/bin``

    * Set the ``ANDROID_SDK_HOME`` directory

      - On macOS: ``~/Library/Android/sdk``

    * Update the SDKs::

        $ sdkmanager --update

    * Create a virtual device image, following `these instructions <https://developer.android.com/studio/run/managing-avds.html>`__.

    ..    $ avdmanager create avd --package "system-images;android-22;google_apis;x86" --device "Nexus 5X" --name Nexus5X

    ..  If prompted about creating a custom hardware profile, answer "No".

    ..  cd $ANDROID_SDK_HOME/tools

    * Install `Gradle <https://gradle.org/>`__.

    * Start the emulator::

        $ emulator @Nexus_5X_API_22

Create a Virtual Environment
----------------------------

We recommend creating a `virtual environment` for your project. A virtual environment is a self-contained packaging of Python where you can install the libraries needed for this project without worrying about conflicting with your other projects.

Run these commands to create the directory for your project and set up the virtual environment:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

        $ mkdir briefcase_tutorial
        $ cd briefcase_tutorial
        $ python3 -m venv venv
        $ . venv/bin/activate

  .. group-tab:: Linux

    .. code-block:: bash

        $ mkdir briefcase_tutorial
        $ cd briefcase_tutorial
        $ python3 -m venv venv
        $ . venv/bin/activate

  .. group-tab:: Windows

    .. code-block:: doscon

        C:\...>mkdir briefcase_tutorial
        C:\...>cd briefcase_tutorial
        C:\...>python3 -m venv venv
        C:\...>venv\Scripts\activate

The last command activates the virtual environment, which means that any
libraries you install at this point will go into this environment.  See the
`Python venv documentation <https://docs.python.org/3/library/venv.html>`_ for
complete documentation of virtual environments.

Install Briefcase
-----------------

You're now ready to install Briefcase:

.. code-block:: bash

    (venv) $ pip install briefcase

Next Steps
----------

You now have a working Briefcase environment, so you can :doc:`start the first
tutorial </tutorial/tutorial-0>`.
