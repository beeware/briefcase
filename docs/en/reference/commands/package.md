# package

Compile/build an application installer. By default, targets the current platform's default output format.

This will produce an installable artefact.

You should not package an application that was built using `build --test` or `build --debug <debugger>`.

## Usage

To build an installer of the default output format for the current platform:

```console
$ briefcase package
```

To build an installer for a different platform:

```console
$ briefcase package <platform>
```

To build an installer for a specific output format:

```console
$ briefcase package <platform> <output format>
```

/// admonition | Packaging tool requirements

Building installers for some platforms depends on the build tools for the platform you're targeting being available on the platform you're using. For example, you will only be able to create iOS applications on macOS. Briefcase will check for any required tools, and will report an error if the platform you're targeting is not supported.

///

## Options

The following options can be provided at the command line.

### `-a <app name>` / `--app <app name>`

Run a specific application target in your project. This argument is only required if your project contains more than one application target. The app name specified should be the machine-readable package name for the app.

### `-u` / `--update`

Update and recompile the application's code before running. Equivalent to running:

```console
$ briefcase update
$ briefcase package
```

### `-p <format>`, `--packaging-format <format>`

The format to use for packaging. The available packaging formats are platform dependent.

### `--adhoc-sign`

Perform the bare minimum signing that will result in a app that can run on your local machine. This may result in no signing, or signing with an ad-hoc signing identity. The `--adhoc-sign` option may be useful during development and testing. However, care should be taken using this option for release artefacts, as it may not be possible to distribute an ad-hoc signed app to others.

### `-i <identity>` / `--identity <identity>`

The [code signing identity][obtain-code-signing-identity] to use when signing the app.

The format for the code signing identity is platform specific:

* **On macOS:** The 40-character hex thumbprint of the signing identity; the full name of the certificate (e.g., `Developer ID Application: Jane Smith (ABC12345DE)`); or `-` to use an ad-hoc signature. See the [documentation on macOS code signing for more details](../../how-to/code-signing/macOS.md).

* **On Windows:** The 40-character hex thumbprint of the signing identity; or the subject name of a certificate in the user's certificate store. See the [documentation on Windows code signing for more details](../../how-to/code-signing/windows.md).
