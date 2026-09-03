# How to run Briefcase

Briefcase can be installed and run in a few different ways depending on your preferred workflow.

## Default installation

The standard way to install Briefcase is into a Python virtual environment. 

1. Create and activate a virtual environment:

    ```bash
    # On macOS and Linux
    python -m venv venv
    source venv/bin/activate
    
    # On Windows
    python -m venv venv
    venv\Scripts\activate
    ```

2. Install Briefcase using `pip`:

    ```bash
    python -m pip install briefcase
    ```

3. Run Briefcase commands:

    ```bash
    briefcase <command>
    ```

For a full list of commands you can run, see the [Command Reference](../reference/commands/index.md). For a more general guide to using Briefcase, check out the [Tutorial](../tutorial/index.md).

## Using `uvx`

If you have [`uv`](https://docs.astral.sh/uv/) installed, you can use `uvx` to download and run Briefcase in a temporary, isolated environment without explicitly installing it first:

```bash
uvx briefcase <command>
```

## Using `pipx`

If you use [`pipx`](https://pipx.pypa.io/) to manage CLI applications, you can install Briefcase globally so it is always available on your command line:

```bash
pipx install briefcase
```

You can then run Briefcase from anywhere:

```bash
briefcase <command>
```

Alternatively, you can use `pipx run` to execute Briefcase without installing it permanently:

```bash
pipx run briefcase <command>
```
