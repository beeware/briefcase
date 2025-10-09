# Windows App folder

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

A Windows App folder is a stub binary, along with a collection of
subfolders that contain the Python code for the app and the Python
runtime libraries.

A Windows App folder is the default Briefcase output format when running
on Windows. However, you can explicitly specify the use of the Windows
App folder backend by using `briefcase <command> windows app`.

All Windows apps, regardless of output format, use the same icon
formats, have the same set of configuration and runtime options, have
the same permissions, and have the same platform quirks. See
[the documentation on Windows apps][windows] for more details.

## Application configuration

Any configuration option specified in the
`tool.briefcase.app.<appname>.windows` section of your `pyproject.toml`
file will be used by the Windows App folder backend. To specify a
setting that will *only* be used by Windows App folders and *not* other
Windows output formats, put the setting in a
`tool.briefcase.app.<appname>.windows.app` section of your
`pyproject.toml`.
