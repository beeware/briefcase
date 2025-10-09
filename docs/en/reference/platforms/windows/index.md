# Windows

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
<td colspan="2">{{ ci_tested }}</td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
</tbody>
</table>

Briefcase supports two output formats for Windows apps:

- A [Windows app folder][windows-app-folder] with a pre-compiled binary;
  and
- A [Visual Studio project][visual-studio-project] which can be used to
  build an app with a customized binary.

The default output format for Windows is a [Windows app folder][windows-app-folder].

Configuration options between the [Windows app folder][windows-app-folder]
and [Visual Studio project][visual-studio-project] formats are
identical.

## Prerequisites  { #windows-prerequisites }

Briefcase requires installing Python 3.10+. You will also need a method for managing virtual environments (such as `venv`).

## Packaging format

Briefcase supports two packaging formats for a Windows app:

1.  As an MSI installer (the default output of
    `briefcase package windows`, or by using
    `briefcase package windows -p msi`); or
2.  As a ZIP file containing all files needed to run the app (by using
    `briefcase package windows -p zip`).

Briefcase uses the [WiX Toolset](https://www.firegiant.com/wixtoolset/)
to build an MSI installer for a Windows app.

## Icon format

Windows apps installers use multi-format `.ico` icons; these icons
should contain images in the following sizes:

- 16px
- 32px
- 48px
- 64px
- 256px

Windows Apps do not support splash screens or installer images.

## Additional options

The following options can be provided at the command line when packaging
Windows apps.

### `--file-digest <digest>`

The digest algorithm to use for code signing files in the project.
Defaults to `sha256`.

### `--use-local-machine-stores`

By default, the certificate for code signing is assumed to be in the
Current User's certificate stores. Use this flag to indicate the
certificate is in the Local Machine's certificate stores.

### `--cert-store <store>`

The internal Windows name for the certificate store containing the
certificate for code signing. Defaults to `My`.

Common Stores:

| Windows internal name | Certificate store type                     |
|-----------------------|--------------------------------------------|
| My                    | Personal                                   |
| CA                    | Intermediate Certification Authorities     |
| AuthRoot              | Third-Party Root Certification Authorities |
| TrustedPeople         | Trusted People                             |
| TrustedPublisher      | Trusted Publishers                         |
| Root                  | Trusted Root Certification Authorities     |

### `--timestamp-url <url>`

The URL of the Timestamp Authority server to timestamp the code signing.
Defaults to `http://timestamp.digicert.com`.

### `--timestamp-digest <url>`

The digest algorithm to request the Timestamp Authority server uses for
the timestamp for code signing. Defaults to `sha256`.

## Application configuration

### `windows`

The following options can be added to the
`tool.briefcase.app.<appname>.windows` section of your `pyproject.toml`
file.

### `system_installer`

Controls whether the app will be installed as a per-user or per-machine
app. Per-machine apps are "system" apps, and require admin permissions
to run the installer; however, they are installed once and shared
between all users on a computer.

If `true` the installer will attempt to install the app as a per-machine
app, available to all users. If `false`, the installer will install as a
per-user app. If undefined the installer will ask the user for their
preference.

### `use_full_install_path`

Controls whether the app will be installed using a path which includes
both the application name *and* the company or developer's name. If
`true` (the default), the app will be installed to
`Program Files<Author Name><Project Name>`. If `false`, it will be
installed to `Program Files<Project Name>`. Using the full path makes
sense for larger companies with multiple applications, but less so for a
solo developer.

### `version_triple`

Python and Briefcase allow any valid [PEP440 version
number](https://peps.python.org/pep-0440/) as a
[`version`][] specifier. However, MSI
installers require a strict integer triple version number. Many
PEP440-compliant version numbers, such as "1.2", "1.2.3b3", and
"1.2.3.4", are invalid for MSI installers.

Briefcase will attempt to convert your [`version`][] into a valid MSI value by extracting the first three parts
of the main series version number (excluding pre, post and dev version
indicators), padding with zeros if necessary:

> - `1.2` becomes `1.2.0`
> - `1.2b4` becomes `1.2.0`
> - `1.2.3b3` becomes `1.2.3`
> - `1.2.3.4` becomes `1.2.3`.

However, if you need to override this default value, you can define
[`version_triple`][] in your app settings. If
provided, this value will be used in the MSI configuration file instead
of the auto-generated value.

## Platform quirks

### Use caution with `--update-support`

Care should be taken when using the `--update-support` option to the
`update`, `build` or `run` commands. Support packages in Windows apps
are overlaid with app content, so it isn't possible to remove all old
support files before installing new ones.

Briefcase will unpack the new support package without cleaning up
existing support package content. This *should* work; however, ensure a
reproducible release artefacts, it is advisable to perform a clean app
build before release.

### Packaging with `--adhoc-sign`

Using the `--adhoc-sign` option on Windows results in no signing being
performed on the packaged app. This will result in your application
being flagged as coming from an unverified publisher. This may limit who
is able to install your app.

### Tkinter is not available

Briefcase uses the official [Python.org Windows Embeddable package](https://docs.python.org/3/using/windows.html#windows-embeddable)
to provide Python binaries for the Windows app. This embeddable
distribution is missing some standard library modules that would be part
of a normal Python.org install - most notably `tkinter`. This is due to
the difficulty in distributing the Tk libraries needed by Tkinter in a
way that is compatible with the Windows embedded binary format.
