# dev

Run the application in developer mode.

## Usage

To run your application in development mode on the current platform's default output format:

```console
$ briefcase dev
```

To run your application for a different platform:

```console
$ briefcase dev <platform>
```

To run your application using a specific output format:

```console
$ briefcase dev <platform> <output format>
```

The first time the application runs in developer mode, any requirements listed in a [`requires`][] configuration item in `pyproject.toml` will be installed into the current environment.

## Options

The following options can be provided at the command line.

### `-a <app name>` / `--app <app name>`

Run a specific application target in your project. This argument is only required if your project contains more than one application target. The app name specified should be the machine-readable package name for the app.

### `-r` / `--update-requirements`

Update application requirements.

### `--no-run`

Do not run the application; only install application requirements.

### `--test`

Run the test suite in the development environment.

### Passthrough arguments

If you want to pass any arguments to your app's command line, you can specify them using the `--` marker to separate Briefcase's arguments from your app's arguments. For example:

```console
$ briefcase dev -- --wiggle --test
```

will run the app in normal mode, passing the `--wiggle` and `--test` flags to the app's command line. The app will *not* run in *Briefcase's* test mode; the `--test` flag will be left for your own app to interpret.

## Environment variables

By default, `briefcase dev` will use the following environment variables:

- `PYTHONDEVMODE=1` activates additional runtime checks, e.g., [`DeprecationWarning`][] (see also [`PYTHONDEVMODE`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONDEVMODE))
- `PYTHONUNBUFFERED=1` forces the `stdout` and `stderr` streams to be unbuffered (see also the Python [`PYTHONUNBUFFERED`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUNBUFFERED))
- `PYTHONUTF8=1` forces the usage of the UTF-8 encoding (see also [`PYTHONUTF8`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUTF8)).

To deactivate this behavior, you can explicitly set the environment variables to empty strings:

- For one command execution on Linux or macOS: `PYTHONDEVMODE= briefcase dev`
- For the current shell on Linux or macOS: `export PYTHONDEVMODE=`
- For the current shell in Windows PowerShell: `$env:PYTHONDEVMODE = ""`
