# How to run Briefcase  { #run-briefcase }

This guide describes how to install and invoke Briefcase as an end-user tool, independent of the [Tutorial][] which walks through creating a full project.

## Prerequisites

Briefcase requires Python 3.10 or later.

You should create and activate a virtual environment before installing Briefcase. If you are not familiar with virtual environments, see the [Python packaging user guide][venv-guide] for an introduction.

## Default install

1. Create and activate a virtual environment:

   ```console
   $ python -m venv ~/.venvs/briefcase
   $ source ~/.venvs/briefcase/bin/activate
   ```

   On Windows, the activation command is:

   ```console
   C:\> %USERPROFILE%\.venvs\briefcase\Scripts\activate
   ```

2. Install Briefcase into the virtual environment:

   ```console
   (briefcase) $ python -m pip install briefcase
   ```

3. Verify the installation:

   ```console
   (briefcase) $ briefcase --version
   ```

4. Invoke Briefcase using any of the commands listed in the [Command reference][commands]:

   ```console
   (briefcase) $ briefcase new
   ```

## Using uvx

[uvx][uvx] is a runner provided by the `uv` tool that executes a Python package in an isolated, temporary environment without requiring a manual virtual environment.

1. Install `uv` following the [official instructions][uv-install].

2. Run Briefcase without any global install:

   ```console
   $ uvx briefcase new
   ```

   Each invocation runs in a fresh environment, so Briefcase itself is not installed into your system Python or any project virtual environment.

## Using pipx

[pipx][pipx] installs Python CLI tools into isolated environments and exposes their commands on your `PATH` so they are available in every shell.

1. Install `pipx` following the [official instructions][pipx-install].

2. Install Briefcase:

   ```console
   $ pipx install briefcase
   ```

3. Invoke Briefcase from any shell:

   ```console
   $ briefcase new
   ```

   Unlike `uvx`, this does a one-time persistent install. Upgrade later with `pipx upgrade briefcase`.

## Where to go next

- Follow the [Tutorial][] to create a complete Briefcase project from scratch.
- Browse the [Command reference][commands] for the full list of Briefcase commands.
- See the [How-to guides index][how-to-index] for packaging, debugging, and publishing tasks.

[ Tutorial ]: ../../tutorial/index.md
[ commands ]: ../../reference/commands.md
[ how-to-index ]: index.md
[ venv-guide ]: https://packaging.python.org/en/latest/guides/installing-packages-from-pip/#creating-and-using-virtual-environments
[ uvx ]: https://docs.astral.sh/uv/guides/tools/
[ uv-install ]: https://docs.astral.sh/uv/getting-started/installation/
[ pipx ]: https://pipx.pypa.io/
[ pipx-install ]: https://pipx.pypa.io/stable/installation/
