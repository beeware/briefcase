==========================================
Building a CLI application with Briefcase
==========================================

Overview
---------

In this tutorial, you'll learn how to build and package a Command Line Interface (CLI) application for distribution on Windows, macOS, and Linux using Briefcase.

Prerequisites
-------------

Before you start, you'll need to have the following installed on your computer:

* Python 3.8 or later
* Briefcase
* A code editor

For more information on installing Briefcase, see the `BeeWare Tutorial <https://docs.beeware.org/en/latest/tutorial/tutorial-0.html>`_.

Bootstrap a new project
------------------------

Let's start our first Briefcase CLI project!
We're going to use the Briefcase ``new`` command to create an application called **Hello World**.
The only thing that we need to change is the GUI framework.
Since we're building a CLI application, we'll select the **Console** GUI framework.
Run the following from your command prompt:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ briefcase new
      Let's build a new Briefcase app!
      -- Formal Name ---------------------------------------------------------------

      First, we need a formal name for your application.

      This is the name that will be displayed to humans whenever the name of the
      application is displayed. It can have spaces and punctuation if you like, and
      any capitalization will be used as you type it.

      Formal Name [Hello World]: Hello World


      -- App Name ------------------------------------------------------------------

      Next, we need a name that can serve as a machine-readable Python package name
      for your application.

      This name must be PEP508-compliant - that means the name may only contain
      letters, numbers, hyphens and underscores; it can't contain spaces or
      punctuation, and it can't start with a hyphen or underscore.

      Based on your formal name, we suggest an app name of 'helloworld', but you can
      use another name if you want.

      App Name [helloworld]: helloworld


      -- Bundle Identifier ---------------------------------------------------------

      Now we need a bundle identifier for your application.

      App stores need to protect against having multiple applications with the same
      name; the bundle identifier is the namespace they use to identify applications
      that come from you. The bundle identifier is usually the domain name of your
      company or project, in reverse order.

      For example, if you are writing an application for Example Corp, whose website
      is example.com, your bundle would be 'com.example'. The bundle will be
      combined with your application's machine readable name to form a complete
      application identifier (e.g., com.example.helloworld).

      Bundle Identifier [com.example]: com.example


      -- Project Name --------------------------------------------------------------

      Briefcase can manage projects that contain multiple applications, so we need a
      Project name.

      If you're only planning to have one application in this project, you can use
      the formal name as the project name.

      Project Name [Hello World]: Hello World


      -- Description ---------------------------------------------------------------

      Now, we need a one line description for your application.

      Description [My first application]: My first application


      -- Author --------------------------------------------------------------------

      Who do you want to be credited as the author of this application?

      This could be your own name, or the name of your company you work for.

      Author [Jane Developer]: Jane Developer


      -- Author's Email ------------------------------------------------------------

      What email address should people use to contact the developers of this
      application?

      This might be your own email address, or a generic contact address you set up
      specifically for this application.

      Author's Email [jane@example.com]: jane@example.com


      -- Application URL -----------------------------------------------------------

      What is the website URL for this application?

      If you don't have a website set up yet, you can put in a dummy URL.

      Application URL [https://example.com/helloworld]: https://example.com/helloworld


      -- Project License -----------------------------------------------------------

      What license do you want to use for this project's code?

        1) BSD license
        2) MIT license
        3) Apache Software License
        4) GNU General Public License v2 (GPLv2)
        5) GNU General Public License v2 or later (GPLv2+)
        6) GNU General Public License v3 (GPLv3)
        7) GNU General Public License v3 or later (GPLv3+)
        8) Proprietary
        9) Other

      Project License [1]: 1


      -- GUI Framework -------------------------------------------------------------

      What GUI toolkit do you want to use for this project?

      Additional GUI bootstraps are available; visit
      https://beeware.org/bee/briefcase-bootstraps for a full list of known GUI
      bootstraps.

        1) Toga
        2) PySide6 (does not support iOS/Android/Web deployment)
        3) Pygame  (does not support iOS/Android/Web deployment)
        4) Console (does not support iOS/Android/Web deployment)
        5) None

      GUI Framework [1]: 4


      ------------------------------------------------------------------------------

      [helloworld] Generating a new application 'Hello World'
      Using app template: https://github.com/beeware/briefcase-template, branch v0.1
      Template branch v0.1 not found; falling back to development template
      Using existing template (sha b7a98f8ef56dce6dc4ec0afb211b475c71caea26, updated Mon Aug 12 07:18:17 2024)

      [helloworld] Generated new application 'Hello World'

      To run your application, type:

          $ cd helloworld
          $ briefcase dev


  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ briefcase new
      Let's build a new Briefcase app!
      -- Formal Name ---------------------------------------------------------------

      First, we need a formal name for your application.

      This is the name that will be displayed to humans whenever the name of the
      application is displayed. It can have spaces and punctuation if you like, and
      any capitalization will be used as you type it.

      Formal Name [Hello World]: Hello World


      -- App Name ------------------------------------------------------------------

      Next, we need a name that can serve as a machine-readable Python package name
      for your application.

      This name must be PEP508-compliant - that means the name may only contain
      letters, numbers, hyphens and underscores; it can't contain spaces or
      punctuation, and it can't start with a hyphen or underscore.

      Based on your formal name, we suggest an app name of 'helloworld', but you can
      use another name if you want.

      App Name [helloworld]: helloworld


      -- Bundle Identifier ---------------------------------------------------------

      Now we need a bundle identifier for your application.

      App stores need to protect against having multiple applications with the same
      name; the bundle identifier is the namespace they use to identify applications
      that come from you. The bundle identifier is usually the domain name of your
      company or project, in reverse order.

      For example, if you are writing an application for Example Corp, whose website
      is example.com, your bundle would be 'com.example'. The bundle will be
      combined with your application's machine readable name to form a complete
      application identifier (e.g., com.example.helloworld).

      Bundle Identifier [com.example]: com.example


      -- Project Name --------------------------------------------------------------

      Briefcase can manage projects that contain multiple applications, so we need a
      Project name.

      If you're only planning to have one application in this project, you can use
      the formal name as the project name.

      Project Name [Hello World]: Hello World


      -- Description ---------------------------------------------------------------

      Now, we need a one line description for your application.

      Description [My first application]: My first application


      -- Author --------------------------------------------------------------------

      Who do you want to be credited as the author of this application?

      This could be your own name, or the name of your company you work for.

      Author [Jane Developer]: Jane Developer


      -- Author's Email ------------------------------------------------------------

      What email address should people use to contact the developers of this
      application?

      This might be your own email address, or a generic contact address you set up
      specifically for this application.

      Author's Email [jane@example.com]: jane@example.com


      -- Application URL -----------------------------------------------------------

      What is the website URL for this application?

      If you don't have a website set up yet, you can put in a dummy URL.

      Application URL [https://example.com/helloworld]: https://example.com/helloworld


      -- Project License -----------------------------------------------------------

      What license do you want to use for this project's code?

        1) BSD license
        2) MIT license
        3) Apache Software License
        4) GNU General Public License v2 (GPLv2)
        5) GNU General Public License v2 or later (GPLv2+)
        6) GNU General Public License v3 (GPLv3)
        7) GNU General Public License v3 or later (GPLv3+)
        8) Proprietary
        9) Other

      Project License [1]: 1


      -- GUI Framework -------------------------------------------------------------

      What GUI toolkit do you want to use for this project?

      Additional GUI bootstraps are available; visit
      https://beeware.org/bee/briefcase-bootstraps for a full list of known GUI
      bootstraps.

        1) Toga
        2) PySide6 (does not support iOS/Android/Web deployment)
        3) Pygame  (does not support iOS/Android/Web deployment)
        4) Console (does not support iOS/Android/Web deployment)
        5) None

      GUI Framework [1]: 4


      ------------------------------------------------------------------------------

      [helloworld] Generating a new application 'Hello World'
      Using app template: https://github.com/beeware/briefcase-template, branch v0.1
      Template branch v0.1 not found; falling back to development template
      Using existing template (sha b7a98f8ef56dce6dc4ec0afb211b475c71caea26, updated Mon Aug 12 07:18:17 2024)

      [helloworld] Generated new application 'Hello World'

      To run your application, type:

          $ cd helloworld
          $ briefcase dev

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>briefcase new
      Let's build a new Briefcase app!
      -- Formal Name ---------------------------------------------------------------

      First, we need a formal name for your application.

      This is the name that will be displayed to humans whenever the name of the
      application is displayed. It can have spaces and punctuation if you like, and
      any capitalization will be used as you type it.

      Formal Name [Hello World]: Hello World


      -- App Name ------------------------------------------------------------------

      Next, we need a name that can serve as a machine-readable Python package name
      for your application.

      This name must be PEP508-compliant - that means the name may only contain
      letters, numbers, hyphens and underscores; it can't contain spaces or
      punctuation, and it can't start with a hyphen or underscore.

      Based on your formal name, we suggest an app name of 'helloworld', but you can
      use another name if you want.

      App Name [helloworld]: helloworld


      -- Bundle Identifier ---------------------------------------------------------

      Now we need a bundle identifier for your application.

      App stores need to protect against having multiple applications with the same
      name; the bundle identifier is the namespace they use to identify applications
      that come from you. The bundle identifier is usually the domain name of your
      company or project, in reverse order.

      For example, if you are writing an application for Example Corp, whose website
      is example.com, your bundle would be 'com.example'. The bundle will be
      combined with your application's machine readable name to form a complete
      application identifier (e.g., com.example.helloworld).

      Bundle Identifier [com.example]: com.example


      -- Project Name --------------------------------------------------------------

      Briefcase can manage projects that contain multiple applications, so we need a
      Project name.

      If you're only planning to have one application in this project, you can use
      the formal name as the project name.

      Project Name [Hello World]: Hello World


      -- Description ---------------------------------------------------------------

      Now, we need a one line description for your application.

      Description [My first application]: My first application


      -- Author --------------------------------------------------------------------

      Who do you want to be credited as the author of this application?

      This could be your own name, or the name of your company you work for.

      Author [Jane Developer]: Jane Developer


      -- Author's Email ------------------------------------------------------------

      What email address should people use to contact the developers of this
      application?

      This might be your own email address, or a generic contact address you set up
      specifically for this application.

      Author's Email [jane@example.com]: jane@example.com


      -- Application URL -----------------------------------------------------------

      What is the website URL for this application?

      If you don't have a website set up yet, you can put in a dummy URL.

      Application URL [https://example.com/helloworld]: https://example.com/helloworld


      -- Project License -----------------------------------------------------------

      What license do you want to use for this project's code?

        1) BSD license
        2) MIT license
        3) Apache Software License
        4) GNU General Public License v2 (GPLv2)
        5) GNU General Public License v2 or later (GPLv2+)
        6) GNU General Public License v3 (GPLv3)
        7) GNU General Public License v3 or later (GPLv3+)
        8) Proprietary
        9) Other

      Project License [1]: 1


      -- GUI Framework -------------------------------------------------------------

      What GUI toolkit do you want to use for this project?

      Additional GUI bootstraps are available; visit
      https://beeware.org/bee/briefcase-bootstraps for a full list of known GUI
      bootstraps.

        1) Toga
        2) PySide6 (does not support iOS/Android/Web deployment)
        3) Pygame  (does not support iOS/Android/Web deployment)
        4) Console (does not support iOS/Android/Web deployment)
        5) None

      GUI Framework [1]: 4


      ------------------------------------------------------------------------------

      [helloworld] Generating a new application 'Hello World'
      Using app template: https://github.com/beeware/briefcase-template, branch v0.1
      Template branch v0.1 not found; falling back to development template
      Using existing template (sha b7a98f8ef56dce6dc4ec0afb211b475c71caea26, updated Mon Aug 12 07:18:17 2024)

      [helloworld] Generated new application 'Hello World'

      To run your application, type:

          $ cd helloworld
          $ briefcase dev

Briefcase will then generate a project skeleton for you to use.
If you've followed this tutorial so far, and accepted the defaults as described,
your file system should look something like::

    beeware-tutorial/
    ├── beeware-venv/
    │   └── ...
    └── helloworld/
        ├── CHANGELOG
        ├── LICENSE
        ├── pyproject.toml
        ├── README.rst
        ├── src/
        │   └── helloworld/
        │       ├── app.py
        │       ├── __init__.py
        │       ├── __main__.py
        │       └── resources/
        │           └── README
        └── tests/
            ├── helloworld.py
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

To run the application in developer (or ``dev``) mode, navigate to the project directory ``helloworld`` and
run the following command:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ cd helloworld
      (venv) $ briefcase dev

      [hello-world] Installing requirements...
      ...

      [helloworld] Starting in dev mode...
      ===========================================================================
      Hello, World.
      ===========================================================================

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ cd helloworld
      (venv) $ briefcase dev

      [hello-world] Installing requirements...
      ...

      [helloworld] Starting in dev mode...
      ===========================================================================
      Hello, World.
      ===========================================================================

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>cd helloworld
      (venv) C:\...>briefcase dev

      [hello-world] Installing requirements...
      ...

      [helloworld] Starting in dev mode...
      ===========================================================================
      Hello, World.
      ===========================================================================

The application will start in the terminal window. You should see a message
that says "Hello, World.".


Now you are ready to start building your CLI application!


Making it interesting
----------------------

Right now the ``app.py`` file contains a simple ``print`` statement that prints "Hello, World.".
Let's use ``argparse`` to make it more interesting.

Replace the contents of ``src/helloworld/app.py`` with the following code:

.. code-block:: python

    import argparse

    def main():
        parser = argparse.ArgumentParser(
            prog="helloworld",
            usage="%(prog)s [options] name",
            description="A simple command line application.",
            add_help=True
        )
        parser.add_argument("name", help="Your name")
        parser.add_argument("-v", "--version", action="version", version="%(prog)s 1.0")
        args = parser.parse_args()
        print(f'Hello, {args.name}!')

Let’s look in detail at what has changed.

1. We import the ``argparse`` module.
2. We define a new function called ``main`` that will contain the logic for our application.
3. We create an instance of ``argparse.ArgumentParser`` and pass in some arguments:
    * ``prog``: The name of the program (in this case, ``helloworld``).
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

    [helloworld] Starting in dev mode...
    ===========================================================================
    usage: helloworld [options] name
    helloworld: error: the following arguments are required: name

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

    [helloworld] Starting in dev mode...
    ===========================================================================
    Hello, John!

Congratulations! You've just built a simple command line application using Briefcase.

Next steps
----------

So far we have been running the application in developer mode. To distribute the application, you will need to package it for distribution.
For more information, see the `Tutorial 3 - Packaging for distribution documentation <https://docs.beeware.org/en/latest/tutorial/tutorial-3.html>`_.
