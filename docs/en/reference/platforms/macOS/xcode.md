# macOS Xcode project

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
<th colspan="11"><a href="../../../../reference/platforms">Host Platform Support</a></th>
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
<td>{{ ci_tested }}</td>
<td>{{ ci_tested }}</td>
<td></td>
<td colspan="2"></td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
</tbody>
</table>

Briefcase supports creating a full Xcode project for a macOS app. This project can then be used to build an app bundle, with the `briefcase build` command or directly from Xcode.

You can specify the use of the macOS Xcode project backend by using `briefcase <command> macOS Xcode`.

Most apps will have no need to use the Xcode format - the [.app bundle][app-bundle] format provides everything that is required to run most macOS apps. The Xcode project format is useful if you need to customize the stub binary that is used to start your app.

All macOS apps, regardless of output format, use the same icon formats, have the same set of configuration and runtime options, have the same permissions, and have the same platform quirks. See [the documentation on macOS apps][macos] for more details.

## Application configuration

Any configuration option specified in the `tool.briefcase.app.<appname>.macOS` section of your `pyproject.toml` file will be used by the macOS Xcode project. To specify a setting that will *only* be used by an Xcode project and *not* other macOS output formats, put the setting in a `tool.briefcase.app.<appname>.macOS.Xcode` section of your `pyproject.toml`.
