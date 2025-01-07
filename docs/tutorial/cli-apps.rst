==========================================
Building a CLI application with Briefcase
==========================================

Overview
--------

In this tutorial, you'll learn how to build and package a Command Line Interface
(CLI) application for distribution on Windows, macOS, and Linux using Briefcase.

We're going to assume you've got an environment set up like you did in the
`Hello, World! tutorial <https://docs.beeware.org/en/latest/tutorial/tutorial-0.html>`_.

Bootstrap a new project
------------------------

Let's start our first Briefcase CLI project! We're going to use the Briefcase
``new`` command to create an application called **Hello CLI**.
Run the following from your command prompt:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ briefcase new

      Let's build a new Briefcase app!
      ...

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ briefcase new

      Let's build a new Briefcase app!
      ...

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>briefcase new

      Let's build a new Briefcase app!
      ...

Briefcase will ask us for some details of our new application. For the
purposes of this tutorial, use the following:

* **Formal Name** - Enter a formal name for your app, for example: ``Hello CLI``.

* **App Name** - Enter a name for your app, for example: ``hello-cli``.

* **Bundle** - If you own your own domain, enter that domain in reversed order.
  (For example, if you own the domain "cupcakes.com", enter ``com.cupcakes``
  as the bundle). If you don't own your own domain, accept the default bundle
  (``com.example``).

* **Project Name** - Accept the default value: ``Hello CLI``.

* **Description** - Accept the default value (or, if you want to be really
  creative, come up with your own description!).

* **Author** - Enter your own name here.

* **Author's email** - Enter your own email address. This will be used in the
  configuration file, in help text, and anywhere that an email is required
  when submitting the app to an app store.

* **URL** - The URL of the landing page for your application. Again, if you own
  your own domain, enter a URL at that domain (including the ``https://``).
  Otherwise, just accept the default URL (``https://example.com/hello-cli``).
  This URL doesn't need to actually exist (for now); it will only be used if
  you publish your application to an app store.

* **License** - Accept the default license (BSD). This won't affect
  anything about the operation of the tutorial, though - so if you have
  particularly strong feelings about license choice, feel free to choose
  another license.

* **GUI framework** - Enter ``4`` to select the **Console** GUI framework. This
  will create a project that is designed to run in a terminal window.

Briefcase will then generate a project skeleton for you to use.
If you've followed this tutorial so far, and accepted the defaults as described,
your file system should look something like::

    tutorial/
    ├── venv/
    │   └── ...
    └── hello-cli/
        ├── .gitignore
        ├── CHANGELOG
        ├── LICENSE
        ├── pyproject.toml
        ├── README.rst
        ├── src/
        │   └── hello_cli/
        │       ├── __init__.py
        │       ├── __main__.py
        │       ├── app.py
        │       └── resources/
        │           └── README
        └── tests/
            ├── __init__.py
            ├── hello_cli.py
            └── test_app.py

The ``src`` folder contains all the code for the application, the
``tests`` folder contains an initial test suite, and the ``pyproject.toml`` file
describes how to package the application for distribution. If you open
``pyproject.toml`` in an editor, you'll see the configuration details you just
provided to Briefcase.

Now that we have a stub application, we can use Briefcase to run the
application.

Running the application in developer mode
------------------------------------------

To run the application in developer (or ``dev``) mode, navigate to the project
directory ``hello-cli`` and run the following command:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ cd hello-cli
      (venv) $ briefcase dev

      [hello-cli] Installing requirements...
      ...

      [hello-cli] Starting in dev mode...
      ===========================================================================
      Hello, World.

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ cd hello-cli
      (venv) $ briefcase dev

      [hello-cli] Installing requirements...
      ...

      [hello-cli] Starting in dev mode...
      ===========================================================================
      Hello, World.

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>cd hello-cli
      (venv) C:\...>briefcase dev

      [hello-cli] Installing requirements...
      ...

      [hello-cli] Starting in dev mode...
      ===========================================================================
      Hello, World.

The application will start in the terminal window. You should see a message
that says "Hello, World.".

Now we are ready to start building our CLI application!

Making it interesting
----------------------

Right now the ``app.py`` file contains a simple ``print`` statement that
prints "Hello, World.". Let's use :any:`argparse` to make it more interesting.

Replace the contents of ``src/hello_cli/app.py`` with the following code:

.. code-block:: python

    import argparse

    def main():
        parser = argparse.ArgumentParser(
            prog="hello-cli",
            usage="%(prog)s [options] name",
            description="A simple command line application.",
            add_help=True
        )
        parser.add_argument("name", help="Your name")
        parser.add_argument("-v", "--version", action="version", version="%(prog)s 1.0")
        args = parser.parse_args()
        print(f'Hello, {args.name}!')

Let's look in detail at what has changed.

1. We import the :any:`argparse` module.
2. We define a new function called ``main`` that will contain the logic for
   our application.
3. We create an instance of :any:`argparse.ArgumentParser` and pass in some arguments:
    * ``prog``: The name of the program (in this case, ``hello-cli``).
    * ``usage``: The usage message that will be displayed when the user runs
      the program with the ``-h`` or ``--help`` flag.
    * ``description``: A description of the program.
    * ``add_help``: Whether to add a ``-h`` or ``--help`` flag to the program.
4. We add two arguments to the parser:
    * ``name``: A positional argument that takes the user's name.
    * ``version``: An optional argument that prints the version of the program.
5. We parse the arguments using ``parser.parse_args()``.
6. We print a message that greets the user by name.

Now that we've made these changes, we can see what they look like by starting
the application again. As before, we'll use developer mode:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ briefcase dev

      [hello-cli] Starting in dev mode...
      ===========================================================================
      usage: hello-cli [options] name
      hello-cli: error: the following arguments are required: name

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ briefcase dev

      [hello-cli] Starting in dev mode...
      ===========================================================================
      usage: hello-cli [options] name
      hello-cli: error: the following arguments are required: name

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>briefcase dev

      [hello-cli] Starting in dev mode...
      ===========================================================================
      usage: hello-cli [options] name
      hello-cli: error: the following arguments are required: name

To pass arguments to the application, we will use the following briefcase
command ``-- ARGS ...``. Let's run the application again, this time with a name:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ briefcase dev -- John

      [hello-cli] Starting in dev mode...
      ===========================================================================
      Hello, John!

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ briefcase dev -- John

      [hello-cli] Starting in dev mode...
      ===========================================================================
      Hello, John!

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>briefcase dev -- John

      [hello-cli] Starting in dev mode...
      ===========================================================================
      Hello, John!

Congratulations! You've just built a simple command line application using
Briefcase.

Packaging for distribution
--------------------------

So far we have been running the application in developer mode.
To distribute the application, you will need to package it for distribution.

Creating your application scaffold
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since this is the first time we're packaging our application, we need to create
some configuration files and other scaffolding to support the packaging process.

From the ``hello-cli`` directory, run:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ briefcase create

      [hello-cli] Generating application template...
      ...

      [hello-cli] Installing support package...
      ...

      [hello-cli] Installing stub binary...
      ...

      [hello-cli] Installing application code...
      Installing src/hello_cli... done

      [hello-cli] Installing requirements...
      ...

      [hello-cli] Installing application resources...

      [hello-cli] Removing unneeded app content...
      Removing unneeded app bundle content... done

      [hello-cli] Created build/hello-cli/macos/app

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ briefcase create

      [hello-cli] Finalizing application configuration...
      ...

      [hello-cli] Generating application template...
      ...

      [hello-cli] Installing support package...
      No support package required.

      [hello-cli] Installing application code...
      Installing src/hello_cli... done

      [hello-cli] Installing requirements...
      ...

      [hello-cli] Installing application resources...
      ...

      [hello-cli] Removing unneeded app content...
      Removing unneeded app bundle content... done

      [hello-cli] Created build/hello-cli/ubuntu/noble

    .. admonition:: Errors about Python versions

      If you receive an error that reads something like:

          The version of Python being used to run Briefcase (3.12) is not the system python3 (3.10).

      You will need to recreate your virtual environment using the system
      ``python3``. Using the system Python is a requirement for packaging your
      application.

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>briefcase create

      [hello-cli] Generating application template...
      ...

      [hello-cli] Installing support package...
      ...

      [hello-cli] Installing stub binary...
      ...

      [hello-cli] Installing application code...
      Installing src/hello_cli... done

      [hello-cli] Installing requirements...
      ...

      [hello-cli] Installing application resources...
      ...

      [hello-cli] Removing unneeded app content...
      ...

      [hello-cli] Created build\hello-cli\windows\app

Once this completes, if you look in the project directory, you should now see a
directory corresponding to your platform (``macOS``, ``linux``, or ``windows``)
that contains additional files. This is the platform-specific packaging
configuration for your application.

Building your application
~~~~~~~~~~~~~~~~~~~~~~~~~

You can now compile your application. This step performs any binary
compilation that is necessary for your application to be executable on your
target platform.

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ briefcase build

      [hello-cli] Building App...

      [hello-cli] Ad-hoc signing app...
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 00:01

      [hello-cli] Built build/hello-cli/macos/app/Hello CLI.app

    On macOS, the ``build`` command doesn't need to *compile* anything, but it
    does need to sign the contents of binary so that it can be executed. This
    signature is an *ad hoc* signature - it will only work on *your* machine; if
    you want to distribute the application to others, you'll need to provide a
    full signature.

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ briefcase build

      [hello-cli] Finalizing application configuration...
      ...

      [hello-cli] Building application...
      ...

      [hello-cli] Built build/hello-cli/ubuntu/noble/hello-cli-0.0.1/usr/bin/hello-cli

    Once this step completes, the ``build`` folder will contain a
    ``hello-cli-0.0.1`` folder that contains a mirror of a Linux ``/usr``
    file system. This file system mirror will contain a ``bin`` folder with a
    ``hello-cli`` binary, plus ``lib`` and ``share`` folders needed to support
    the binary.

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>briefcase build

      [hello-cli] Building App...
      ...

      [hello-cli] Built build\hello-cli\windows\app\src\hello-cli.exe

    On Windows, the ``build`` command doesn't need to *compile* anything, but
    it does need to write some metadata so that the application knows its name,
    version, and so on.

    .. admonition:: Triggering antivirus

      Since this metadata is being written directly in to the pre-compiled
      binary rolled out from the template during the ``create`` command, this
      may trigger antivirus software running on your machine and prevent the
      metadata from being written. In that case, instruct the antivirus to
      allow the tool (named ``rcedit-x64.exe``) to run and re-run the command
      above.

Running your app
~~~~~~~~~~~~~~~~

You can now use Briefcase to run your application:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ briefcase run

      [hello-cli] Starting app...
      ===========================================================================
      usage: hello-cli [options] name
      hello-cli: error: the following arguments are required: name

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ briefcase run

      [hello-cli] Finalizing application configuration...
      ...

      [hello-cli] Starting app...
      ===========================================================================
      usage: hello-cli [options] name
      hello-cli: error: the following arguments are required: name

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>briefcase run

      [hello-cli] Starting app...
      ===========================================================================
      usage: hello-cli [options] name
      hello-cli: error: the following arguments are required: name

This will start to run your console application, using the app bundle created by
the ``build`` command.

Building your installer
~~~~~~~~~~~~~~~~~~~~~~~~

You can now package your application for distribution, using the ``package``
command. The package command does any compilation that is required to convert
the scaffolded project into a final, distributable product. Depending on the
platform, this may involve compiling an installer, performing code signing,
or doing other pre-distribution tasks.

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ briefcase package --adhoc-sign

      [hello-cli] Signing app...

      *************************************************************************
      ** WARNING: Signing with an ad-hoc identity                            **
      *************************************************************************

          This app is being signed with an ad-hoc identity. The resulting
          app will run on this computer, but will not run on anyone else's
          computer.

          To generate an app that can be distributed to others, you must
          obtain an application distribution certificate from Apple, and
          select the developer identity associated with that certificate
          when running 'briefcase package'.

      *************************************************************************

      Signing app with ad-hoc identity...
           ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 00:01

      [hello-cli] Building PKG...
      ...
      Building Hello CLI-0.0.1.pkg... done

      [hello-cli] Packaged dist/Hello CLI-0.0.1.pkg

    The ``dist`` folder will contain a file named ``Hello CLI-0.0.1.pkg``.
    This file is a macOS package file that can be distributed to other macOS
    users. This file will be signed with an ad-hoc signature, which means it
    will only run on your machine.

    You can double click on the ``.pkg`` file to install the application on your
    machine.

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ briefcase package

      [hello-cli] Finalizing application configuration...
      ...

      [hello-cli] Building .deb package...
      ...

      [hello-cli] Packaged dist/hello-cli-0.0.1-1~ubuntu-noble_amd64.deb

    The ``dist`` folder will contain a file named ``hello-cli-0.0.1-1~ubuntu-noble_amd64.deb``.
    This file is a Debian package file that can be distributed to other Linux
    users. This file will be signed with an ad-hoc signature, which means it
    will only run on your machine.

    You can install the package by running:

    .. code-block:: console

      $ sudo dpkg -i dist/hello-cli-0.0.1-1~ubuntu-noble_amd64.deb

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>briefcase package

      *************************************************************************
      ** WARNING: No signing identity provided                               **
      *************************************************************************

          Briefcase will not sign the app. To provide a signing identity,
          use the `--identity` option; or, to explicitly disable signing,
          use `--adhoc-sign`.

      *************************************************************************

      [hello-cli] Building MSI...
      ...

      [hello-cli] Packaged dist/Hello CLI-0.0.1.msi

    The ``dist`` folder will contain a file named ``Hello CLI-0.0.1.msi``.
    This file is a Windows Installer file that can be distributed to other
    Windows users. This file will not be signed, which means it will only run
    on your machine.

    You can double click on the ``.msi`` file to install the application on your
    machine.


Running your installed app
--------------------------

After installing the application, you can run it from the command line:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      $ hello-cli John
      Hello, John!

  .. group-tab:: Linux

    .. code-block:: console

      $ hello-cli John
      Hello, John!

  .. group-tab:: Windows

    .. code-block:: doscon

      C:\...>hello-cli John
      Hello, John!

Congratulations! You've just built a simple command line application using
Briefcase, and packaged it for distribution.

What's next?
------------

This tutorial has shown you how to build a simple command line application using
Briefcase. You can now use Briefcase to build more complex applications, or
explore the other tutorials in the :doc:`Briefcase How-To Guides <../how-to/index>`.
