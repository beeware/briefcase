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

When prompted to select a GUI framework, enter ``4`` to choose **Console**.
This changes how Briefcase structures the app and configures the project.

The most important change is that your ``pyproject.toml`` will include:

.. code-block:: toml

    console_app = true

This flag informs Briefcase to treat the app as a terminal-based (non-GUI) application.
Console apps print to the terminal directly, unlike GUI apps which log to the system
console or display windows.

Inspecting the File Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Your generated project will have a layout similar to:

.. code-block:: text

    hello-cli/
    ├── pyproject.toml
    ├── src/
    │   └── hello_cli/
    │       ├── __main__.py
    │       └── app.py
    └── ...

Note the ``app.py`` file contains a simple ``print("Hello, World.")`` statement by default.

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

Update your ``app.py`` file with this logic. You can now pass a name when running the app:

.. code-block:: console

    $ briefcase dev -- John
    ===========================================================================
    Hello, John!

Packaging and Distribution
---------------------------

Once you've tested your app, you can package it for distribution using:

.. code-block:: console

    $ briefcase create
    $ briefcase build
    $ briefcase package

For **macOS**, console apps are packaged as ``.pkg`` files, rather than the ``.app``
bundles used for GUI apps. This is another major distinction.

.. code-block:: console

    $ briefcase package --adhoc-sign
    ...
    [hello-cli] Packaged dist/Hello CLI-0.0.1.pkg

This ``.pkg`` file installs the app globally, and it can run from the terminal:

.. code-block:: console

    $ hello-cli John
    Hello, John!

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
or any other Python CLI framework.
