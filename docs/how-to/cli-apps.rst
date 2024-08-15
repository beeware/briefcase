==========================================
Building a CLI application with Briefcase
==========================================

Overview
---------

In this tutorial, you'll learn how to build and package a Command Line Interface (CLI) application for distribution on Windows, macOS, and Linux using Briefcase.

We're going to assume you've got an environment set up like you did in the `Hello, World! tutorial <https://docs.beeware.org/en/latest/tutorial/tutorial-0.html>`_.


Bootstrap a new project
------------------------

Let's start our first Briefcase CLI project!
We're going to use the Briefcase ``new`` command to create an application called **Hello CLI**.
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

* **Formal Name** - Accept the default value: ``Hello CLI``.

* **App Name** - Accept the default value: ``hello-cli``.

* **Bundle** - If you own your own domain, enter that domain in reversed order.
  (For example, if you own the domain "cupcakes.com", enter ``com.cupcakes``
  as the bundle). If you don't own your own domain, accept the default bundle
  (``com.example``).

* **Project Name** - Accept the default value: ``Hello CLI``.

* **Description** - Accept the default value (or, if you want to be really
  creative, come up with your own description!)

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
        ├── CHANGELOG
        ├── LICENSE
        ├── pyproject.toml
        ├── README.rst
        ├── src/
        │   └── hello_cli/
        │       ├── app.py
        │       ├── __init__.py
        │       ├── __main__.py
        │       └── resources/
        │           └── README
        └── tests/
            ├── hello_cli.py
            ├── __init__.py
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

To run the application in developer (or ``dev``) mode, navigate to the project directory ``hello-cli`` and
run the following command:

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
      ===========================================================================

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ cd hello-cli
      (venv) $ briefcase dev

      [hello-cli] Installing requirements...
      ...

      [hello-cli] Starting in dev mode...
      ===========================================================================
      Hello, World.
      ===========================================================================

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>cd hello-cli
      (venv) C:\...>briefcase dev

      [hello-cli] Installing requirements...
      ...

      [hello-cli] Starting in dev mode...
      ===========================================================================
      Hello, World.
      ===========================================================================

The application will start in the terminal window. You should see a message
that says "Hello, World.".

Now you are ready to start building your CLI application!


Making it interesting
----------------------

Right now the ``app.py`` file contains a simple ``print`` statement that prints "Hello, World.".
Let's use :any:`argparse` to make it more interesting.

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

1. We import the  :any:`argparse` module.
2. We define a new function called ``main`` that will contain the logic for our application.
3. We create an instance of  :any:`argparse.ArgumentParser`  and pass in some arguments:
    * ``prog``: The name of the program (in this case, ``hello-cli``).
    * ``usage``: The usage message that will be displayed when the user runs the program with the ``-h`` or ``--help`` flag.
    * ``description``: A description of the program.
    * ``add_help``: Whether to add a ``-h`` or ``--help`` flag to the program.
4. We add two arguments to the parser:
    * ``name``: A positional argument that takes the user's name.
    * ``version``: An optional argument that prints the version of the program.
5. We parse the arguments using ``parser.parse_args()``.
6. We print a message that greets the user by name.


Now that we've made these changes we can see what they look like by starting the application again.
As before, we'll use developer mode:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ briefcase dev

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ briefcase dev

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>briefcase dev

When you run the application, you should see the following output:

.. code-block:: console

    [hello-cli] Starting in dev mode...
    ===========================================================================
    usage: hello-cli [options] name
    hello-cli: error: the following arguments are required: name

To pass arguments to the application, we will use the the following briefcase command  ``-- ARGS ...``
Let's run the application again, this time with a name:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ briefcase dev -- John

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ briefcase dev -- John

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>briefcase dev -- John

Now you should see the following output:

.. code-block:: console

    [hello-cli] Starting in dev mode...
    ===========================================================================
    Hello, John!

Congratulations! You've just built a simple command line application using Briefcase.

Next steps
----------

So far we have been running the application in developer mode. To distribute the application, you will need to package it for distribution.
For more information, see the `Tutorial 3 - Packaging for distribution documentation <https://docs.beeware.org/en/latest/tutorial/tutorial-3.html>`_.
