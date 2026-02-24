# publish

Uploads your application to a [publication channel][publication-channel-interface]. By default, targets the current platform's default output format.

You may need to provide additional configuration details (e.g., authentication credentials), depending on the publication channel selected.

## Usage

To publish the application artefacts for the current platform's default output format to the default publication channel:

```console
$ briefcase publish
```

To publish the application artefacts for a different platform:

```console
$ briefcase publish <platform>
```

To publish the application artefacts for a specific output format:

```console
$ briefcase publish <platform> <output format>
```

## Options

The following options can be provided at the command line.

### `-a <app name>` / `--app <app name>`

Publish a specific application target in your project. This argument is only required if your project contains more than one application target. The app name specified should be the machine-readable package name for the app.

### `-u` / `--update`

Update and recompile the application's code before publication. Equivalent to running:

```console
$ briefcase update
$ briefcase package
$ briefcase publish
```

### `-p <format>`, `--packaging-format <format>`

The format to use for packaging. The available packaging formats are platform dependent.

### `-c <channel>` / `--channel <channel>`

Nominate a [publication channel][publication-channel-interface] to use.

--8<-- "_snippets/no-channels-note.md"

## Platform guides

For platform-specific publishing workflows, see the how-to guides for [Android](../../how-to/publishing/android.md), [iOS](../../how-to/publishing/iOS.md), and [macOS](../../how-to/publishing/macOS.md).
