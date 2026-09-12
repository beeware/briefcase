# How to install and run Briefcase

Briefcase can be installed and run in a few different ways depending on your preferred workflow.

/// admonition | First time?

If this is your first time using Briefcase, you probably want to run through the [BeeWare tutorial](https://tutorial.beeware.org). This tutorial will walk you through the process of building a complete Python application, including deploying it to multiple platforms.

///

## Default installation

The standard way to install Briefcase is into a Python virtual environment.

1. Create and activate a virtual environment:

/// tab | macOS

```console
$ python -m venv venv
$ source venv/bin/activate
```

///

/// tab | Linux

```console
$ python -m venv venv
$ source venv/bin/activate
```

///


/// tab | Windows

```doscon
C:\...>py -m venv venv
C:\...>venv\Scripts\activate
```

///

2. Install Briefcase using `pip`:

/// tab | macOS

```console
(venv) $ python -m pip install briefcase
```

///

/// tab | Linux

```console
(venv) $ python -m pip install briefcase
```

///


/// tab | Windows

```doscon
(venv) C:\...>py -m pip install briefcase
```

///

3. Run Briefcase commands:

/// tab | macOS

```console
(venv) $ briefcase new
(venv) $ briefcase create
(venv) $ briefcase build
(venv) $ briefcase run
```

///

/// tab | Linux

```console
(venv) $ briefcase new
(venv) $ briefcase create
(venv) $ briefcase build
(venv) $ briefcase run
```

///


/// tab | Windows

```doscon
(venv) C:\...>briefcase new
(venv) C:\...>briefcase create
(venv) C:\...>briefcase build
(venv) C:\...>briefcase run
```

///

For a full list of commands you can run, see the [Command Reference](../reference/commands/index.md).

## Using `uvx`

If you have [`uv`](https://docs.astral.sh/uv/) installed, you can use `uvx` to download and run Briefcase in a temporary, isolated environment without explicitly installing it first:

```bash
$ uvx briefcase new
$ uvx briefcase create
$ uvx briefcase run
```

## Using `pipx`

If you use [`pipx`](https://pipx.pypa.io/) to manage CLI applications, you can install Briefcase globally so it is always available on your command line:

```bash
pipx install briefcase
```

You can then run Briefcase from anywhere:

```bash
$ briefcase new
$ briefcase create
$ briefcase run
```

Alternatively, you can use `pipx run` to execute Briefcase without installing it permanently:

```bash
$ pipx run briefcase new
$ pipx run briefcase create
$ pipx run briefcase run
```
