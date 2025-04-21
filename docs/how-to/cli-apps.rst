=========================================
Building your Console App with Briefcase
=========================================

Overview
--------

This guide explains the key differences when creating a **console application**
using Briefcase, as opposed to a GUI-based app. It assumes you are already familiar
with the basics of Briefcase and have completed the
`BeeWare Tutorial <https://docs.beeware.org/en/latest/tutorial/tutorial-0.html>`_.

We'll cover:

1. How selecting "Console" changes your project configuration
2. The ``console_app`` flag in ``pyproject.toml``
3. How Briefcase handles command-line arguments
4. Operational differences in how console apps run and display output
5. Packaging differences specific to console apps (e.g., .pkg bundles on macOS)

Creating a Console App
-----------------------

Start by generating a new Briefcase project with:

.. code-block:: console

    $ briefcase new

When prompted to select a GUI framework, choose the option corresponding to **Console**.
The exact number may vary depending on the plugins installed in your environment.
This changes the code that Briefcase generates for the new app, and the configuration
for the new project.

The most important change is that your ``pyproject.toml`` will include:

.. code-block:: toml

    console_app = true

This flag informs Briefcase to treat the app as a terminal-based (non-GUI) application.
Console apps print to the terminal directly, unlike GUI apps which log to the system
console or display windows.

Inspecting the File Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Your generated project will have a layout similar to the following, assuming your app's
formal name is `Hello CLI` and its app name is `hello-cli`:

.. code-block:: text

    hello-cli/
    ├── pyproject.toml
    ├── src/
    │   └── hello_cli/
    │       ├── __main__.py
    │       └── app.py
    └── ...

Note the ``app.py`` file contains a simple ``print("Hello, World.")`` statement by default.

Handling Command-line Arguments
-------------------------------

You can use any standard Python tool to parse CLI arguments. Here's a simple example
using :any:`argparse`:

.. code-block:: python

    import argparse

    def main():
        parser = argparse.ArgumentParser(description="A simple CLI app.")
        parser.add_argument("name", help="Your name")
        args = parser.parse_args()

        print(f"Hello, {args.name}!")

Update your ``app.py`` file with this logic. You can now pass a name when running the app.

Running the App with Briefcase
------------------------------

Briefcase provides two ways to run your app: ``dev`` mode and ``run`` mode.
You can pass command-line arguments to your app in both cases using ``--`` followed
by your arguments.

For example, running in dev mode:

.. code-block:: console

    $ briefcase dev -- John
    ===========================================================================
    Hello, John!

And similarly after packaging:

.. code-block:: console

    $ briefcase run -- John
    ===========================================================================
    Hello, John!

This is a key difference from GUI apps, which are usually launched without passing
arguments and display a graphical window.

Packaging and Distribution
---------------------------

Once you've tested your app, you can package it for distribution using:

.. code-block:: console

    $ briefcase create
    $ briefcase build
    $ briefcase package

On **macOS**, console apps *must* be packaged as ``.pkg`` files, rather than the
``.app`` or ``.dmg`` bundles used for GUI apps. This is required to install a
entry on the user's path so that the app can be executed from the command line.

.. code-block:: console

    $ briefcase package --adhoc-sign
    ...
    [hello-cli] Packaged dist/Hello CLI-0.0.1.pkg

This ``.pkg`` file installs the app globally, and it can run from the terminal:

.. code-block:: console

    $ hello-cli John
    Hello, John!

.. note::

    The executable name of your app will be the app name, not the formal name.
    For example, in this guide, the formal name is `Hello CLI`, but the executable
    name is `hello-cli`. This is the name you will use to run your app from the
    terminal, as shown in the examples above.

On **Linux**, you'll get a ``.deb`` package, and on **Windows**, a ``.msi`` installer.

Console App Behavior Summary
----------------------------

Key differences from GUI apps include:

- **Project structure** includes ``console_app = true`` in ``pyproject.toml``
- **Apps are executed in the terminal**, and print directly to stdout
- **Arguments are passed using** ``-- ARGS ...`` when using ``briefcase dev`` and ``briefcase run``
- **No GUI framework or windowing system** is used or bundled
- **macOS packaging uses ``.pkg`` format**, rather than GUI `.app` bundles

What's next?
------------

Now that you've built a simple console app with Briefcase, you can use these
principles to build more complex CLI tools or integrate other libraries like
`Click <https://click.palletsprojects.com/>`_, `Typer <https://typer.tiangolo.com/>`_,
or any other Python CLI framework. For more advanced text-based interfaces, you
might also explore libraries like `curses <https://docs.python.org/3/library/curses.html>`_
or `Textual <https://textual.textualize.io/>`_, which allow you to create "GUI-like"
applications in the terminal.
