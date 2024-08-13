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

      $ briefcase new
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

      $ briefcase new
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

      C:\...>briefcase new
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

This skeleton is actually a fully functioning application without adding
anything else. The ``src`` folder contains all the code for the application, the
``tests`` folder contains an initial test suite, and the ``pyproject.toml`` file
describes how to package the application for distribution. If you open
``pyproject.toml`` in an editor, you'll see the configuration details you just
provided to Briefcase.

Now that we have a stub application, we can use Briefcase to run the
application.


Running the application in developer mode
------------------------------------------

To run the application in developer (or ``dev``) mode, navigate to the project directory ``helloworld``` and
run the following command:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (beeware-venv) $ cd helloworld
      (beeware-venv) $ briefcase dev

      [hello-world] Installing requirements...
      ...

      [helloworld] Starting in dev mode...
      ===========================================================================

  .. group-tab:: Linux

    .. code-block:: console

      (beeware-venv) $ cd helloworld
      (beeware-venv) $ briefcase dev

      [hello-world] Installing requirements...
      ...

      [helloworld] Starting in dev mode...
      ===========================================================================

  .. group-tab:: Windows

    .. code-block:: doscon

      (beeware-venv) C:\...>cd helloworld
      (beeware-venv) C:\...>briefcase dev

      [hello-world] Installing requirements...
      ...

      [helloworld] Starting in dev mode...
      ===========================================================================

The application will start in a new terminal window. You should see a message
that says "Hello, world!".


Now you are ready to start building and packaging CLI apps! Have fun!
