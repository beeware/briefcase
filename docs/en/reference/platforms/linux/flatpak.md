# Flatpak

<table class="host-platform-support-table">
<colgroup>
<col style="width: 11%" />
<col style="width: 10%" />
<col style="width: 7%" />
<col style="width: 5%" />
<col style="width: 6%" />
<col style="width: 5%" />
<col style="width: 5%" />
<col style="width: 7%" />
<col style="width: 11%" />
<col style="width: 7%" />
<col style="width: 10%" />
</colgroup>
<thead>
<tr>
<th colspan="11"><a href="/reference/platforms/#platform-support-key">Host Platform Support</a></th>
</tr>
<tr>
<th colspan="2">macOS</th>
<th colspan="5">Windows</th>
<th colspan="4">Linux</th>
</tr>
<tr>
<th>x86‑64</th>
<th>arm64</th>
<th>x86</th>
<th colspan="2">x86‑64</th>
<th colspan="2">arm64</th>
<th>x86</th>
<th>x86‑64</th>
<th>arm</th>
<th>arm64</th>
</tr>
</thead>
<tbody>
<tr>
<td></td>
<td></td>
<td></td>
<td colspan="2"></td>
<td colspan="2"></td>
<td>{{ not_tested }}</td>
<td>{{ ci_tested }}</td>
<td>{{ not_tested }}</td>
<td>{{ ci_tested }}</td>
</tr>
</tbody>
</table>

[Flatpak](https://flatpak.org) provides a way for developers to
distribute apps to Linux users in a format that is independent of the
specific distribution used by the end-user. It allow packaging
applications for use on any common Linux distribution, including Ubuntu,
Debian, Fedora, and more. There are some system packages needed to run
and build Flatpaks; see the [Flatpak setup
guide](https://flatpak.org/setup) for more details.

A Flatpak app is built by compiling against a `runtime`. Runtimes
provide the basic dependencies that are used by applications. Each
application must be built against a runtime, and this runtime must be
installed on a host system in order for the application to run (Flatpak
can automatically install the runtime required by an application).

The end user will install the Flatpak into their local app repository;
this can be done by installing directly from a single file `.flatpak`
bundle, or by installing from a package repository like
[Flathub](https://flathub.org). Apps can be installed into user-space,
or if the user has sufficient privileges, they can be installed into a
system-wide app repository.

Briefcase currently supports creating `.flatpak` single file bundles;
end users can install the app bundle by running:

```console
$ flatpak install --user App_Name-1.2.3-x86_64.flatpak
```

substituting the name of the flatpak file as appropriate. The `--user`
option can be omitted if the user wants to install the app system-wide.

The app can then be run with:

```console
$ flatpak run com.example.appname
```

specifying the app bundle identifier as appropriate.

Briefcase *can* be published to Flathub or another Flatpak repository;
but Briefcase does not currently support automated publication of apps.

## Icon format

Flatpak uses `.png` format icons. An application must provide icons in
the following sizes:

- 16px
- 32px
- 64px
- 128px
- 256px
- 512px

Flatpaks do not support splash screens or installer images.

## Application configuration

The following options can be added to the
`tool.briefcase.app.<appname>.linux.flatpak` section of your
`pyproject.toml` file:

### `finish_arg`

The arguments used to configure the Flatpak sandbox. `finish_arg` is an
attribute that can have additional sub-attributes; each sub-attribute
maps to a single property that will be added to the app's manifest. For
example, to add `--allow=bluetooth` as a finish argument, you would
specify:

    finish_arg."allow=bluetooth" = true

Briefcase adds the following finish arguments by default:

- `share=ipc`
- `socket=x11`
- `nosocket=wayland`
- `share=network`
- `device=dri`
- `socket=pulseaudio`
- `filesystem=xdg-cache`
- `filesystem=xdg-config`
- `filesystem=xdg-data`
- `filesystem=xdg-documents`
- `socket=session-bus`

These can be disabled by explicitly setting their value to `False`; for
example, to disable audio access, you would specify:

```python
finish_arg."socket=pulseaudio" = false
```

### `flatpak_runtime_repo_alias`

An alias to use when registering the Flatpak repository that will store
the Flatpak runtime used to build the app. By default, Briefcase will
use [Flathub](https://flathub.org) as its runtime repository, with an
alias of `flathub`.

### `flatpak_runtime_repo_url`

The repository URL hosting the runtime and SDK package that the Flatpak
will use. By default, Briefcase will use [Flathub](https://flathub.org)
as its runtime repository.

### `flatpak_runtime`

A string, identifying the
[runtime](https://docs.flatpak.org/en/latest/available-runtimes.html) to
use as a base for the Flatpak app.

The Flatpak runtime and SDK are paired; so, both a
[`flatpak_runtime`][] and a corresponding
[`flatpak_sdk`][] must be defined.

### `flatpak_runtime_version`

A string, identifying the version of the Flatpak runtime that should be
used.

### `flatpak_base`

An optional string, identifying the
[base](https://docs.flatpak.org/en/latest/flatpak-builder-command-reference.html#flatpak-manifest)
to use as a base for the Flatpak app. A base is a set of extensions
layered on top of a runtime image, providing additional functionality
for the packaged application. Some GUI frameworks (e.g., PyQt) provide a
base image to ensure common required resources are available at runtime.

### `flatpak_base_version`

An optional string (required if [`flatpak_base`][] is defined), identifying the version of the Flatpak base
that should be used.

### `flatpak_sdk`

A string, identifying the SDK associated with the platform that will be
used to build the Flatpak app.

The Flatpak runtime and SDK are paired; so, both a
[`flatpak_runtime`][] and a corresponding
[`flatpak_sdk`][] must be defined.

### `modules_extra_content`

Additional build instructions that will be inserted into the Flatpak
manifest, *after* Python has been installed and `pip` is guaranteed to
exist, but *before* any app code or app packages have been installed
into the Flatpak.

## Permissions

Permissions are not used for Flatpak packaging.

## Compilation issues with Flatpak

Flatpak works by building a sandbox in which to compile the application
bundle. This sandbox uses some low-level kernel and file system
operations to provide the sandboxing behavior. As a result, Flatpaks
cannot be built inside a Docker container, and they cannot be build on
an NFS mounted drive.

If you get errors about `renameat` when building an app, similar to the
following:

```console
[helloworld] Building Flatpak...
Downloading sources
Initializing build dir
Committing stage init to cache
Error: Writing metadata object: renameat: Operation not permitted
Building...

Error while building app helloworld.

Log saved to ...
```

you may be building on an NFS drive. Move your project to local storage,
and retry the build.
