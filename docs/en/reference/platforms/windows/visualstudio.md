# Visual Studio project

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

Briefcase supports creating a full Visual Studio project for a Windows app. This project can then be used to build the stub app binary with the `briefcase build` command, or directly from Visual Studio.

You can specify the use of the Windows Visual Studio project backend by using `briefcase <command> windows visualstudio`.

Most apps will have no need to use the Visual Studio project format - the [Windows app folder][windows-app-folder] format provides everything that is required to run most Windows apps. The Visual Studio project format is useful if you need to customize the stub binary that is used to start your app.

All Windows apps, regardless of output format, use the same icon formats, have the same set of configuration and runtime options, have the same permissions, and have the same platform quirks. See [the documentation on Windows apps][windows] for more details.

## Pre-requisites

Building the Visual Studio project requires that you install Visual Studio 2022 or later. Visual Studio 2022 Community Edition [can be downloaded for free from Microsoft](https://visualstudio.microsoft.com/vs/community/). You can also use the Professional or Enterprise versions if you have them.

Briefcase will auto-detect the location of your Visual Studio installation, provided one of the following three things are true:

1. You install Visual Studio in the standard location in your Program Files folder.
2.  `MSBuild.exe` is on your path.
3. You define the environment variable `MSBUILD` that points at the location of your `MSBuild.exe` executable.

When you install Visual Studio, there are many optional components. You should ensure that you have installed the following:

- .NET Desktop Development
  - All default packages
- Desktop Development with C++
  - All default packages
  - C++/CLI support for v143 build tools

## Application configuration

Any configuration option specified in the `tool.briefcase.app.<appname>.windows` section of your `pyproject.toml` file will be used by the Windows Visual Studio project. To specify a setting that will *only* be used by a Visual Studio project and *not* other Windows output formats, put the setting in a `tool.briefcase.app.<appname>.windows.visualstudio` section of your `pyproject.toml`.
