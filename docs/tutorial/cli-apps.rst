==========================================
Building a CLI application with Briefcase
==========================================

Overview
--------

In this tutorial, you'll learn how to build and package a Command Line Interface
(CLI) application for distribution on Windows, macOS, and Linux using Briefcase.

We're going to assume you've got an environment set up like you did in the
`Hello, World! tutorial 0 <https://docs.beeware.org/en/latest/tutorial/tutorial-0.html>`_.

Bootstrap a new project
------------------------

Let's start our first Briefcase CLI project! We're going to use the Briefcase
``new`` command to create an application called **Hello CLI**.

Similar to what you did in the
`Hello, World! tutorial 1 <https://docs.beeware.org/en/latest/tutorial/tutorial-1.html>`_,
but enter ``4`` for the **GUI framework** to select **Console** rather than **Toga**
as the GUI framework.

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
provided to Briefcase including the ``console_app = true`` setting to indicate
that this is a console application.

If you chose to use an ``App Name`` like **hello-cli**, Briefcase will transform
the name to a valid Python module name by replacing dashes with underscores.
This is why the folder is named ``hello_cli`` While the parent folder holds the
same name as the ``App Name`` i.e. **hello-cli**.

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
that says "Hello, World.". Console applications don't have a GUI, so the
output will be displayed in the terminal window.

Now we are ready to start building our CLI application!

Making it interesting
----------------------

Right now the ``app.py`` file contains a simple ``print`` statement that
prints "Hello, World.". Let's use :any:`argparse` to make it more interesting.
:any:`argparse` is a module in the Python standard library that makes it easy
to write user-friendly command line interfaces. You can use any other library
that you prefer, as long as it can parse command line arguments.

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

Creating and building your application scaffold
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since this is the first time we're packaging our application, we need to create
some configuration files and other scaffolding to support the packaging process.

Similar to what you did in the
`Hello, World! tutorial 3 <https://docs.beeware.org/en/latest/tutorial/tutorial-3.html>`_,
Run the ``briefcase create`` command from the ``hello-cli`` directory, followed by the
``briefcase build`` command to compile the application.

Running your app
~~~~~~~~~~~~~~~~

You can now use Briefcase to run your application. The ``run`` command will
start your application using the app bundle created by the ``build`` command.
Similar to the ``dev`` command, you can pass arguments to the application using
the ``-- ARGS ...`` syntax.

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ briefcase run -- John

      [hello-cli] Starting app...
      ===========================================================================
      Hello, John!

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ briefcase run -- John

      [hello-cli] Finalizing application configuration...
      ...

      [hello-cli] Starting app...
      ===========================================================================
      Hello, John!

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>briefcase run -- John

      [hello-cli] Starting app...
      ===========================================================================
      Hello, John!

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

If you look in the ``dist`` folder, you will see the installer file that was
created. For macOS it will be a ``.pkg`` file, for Linux it will be a ``.deb``
file, and for Windows it will be a ``.msi`` file.

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
