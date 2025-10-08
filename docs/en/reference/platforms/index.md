# Platform support {#platform-support-key}

::: {.toctree hidden=""}
macOS/index windows/index linux/index iOS/index android/index web/index
:::

|                       |                                     |
|-----------------------|-------------------------------------|
| [\|f\|](##SUBST##|f|) | Supported and tested in CI          |
| [\|y\|](##SUBST##|y|) | Supported and tested by maintainers |
| [\|v\|](##SUBST##|v|) | Supported but not tested regularly  |

<table style="width:90%;">
<colgroup>
<col style="width: 9%" />
<col style="width: 16%" />
<col style="width: 8%" />
<col style="width: 7%" />
<col style="width: 5%" />
<col style="width: 3%" />
<col style="width: 4%" />
<col style="width: 3%" />
<col style="width: 3%" />
<col style="width: 5%" />
<col style="width: 8%" />
<col style="width: 5%" />
<col style="width: 7%" />
</colgroup>
<thead>
<tr>
<th colspan="2" rowspan="3">Target App Format</th>
<th colspan="11">Host System</th>
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
<td>Android</td>
<td><a
href="./android/gradle.html"><strong>Gradle project</strong></a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
<td></td>
<td colspan="2"><a href="##SUBST##|f|">|f|</a></td>
<td colspan="2"></td>
<td><a href="##SUBST##|v|">|v|</a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
<td><a href="##SUBST##|v|">|v|</a></td>
<td><a href="##SUBST##|v|">|v|</a></td>
</tr>
<tr>
<td>iOS</td>
<td><a href="./iOS/xcode.html"><strong>Xcode project</strong></a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
<td></td>
<td colspan="2"></td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td rowspan="3">Linux</td>
<td><a href="./linux/appimage.html">AppImage</a></td>
<td><a href="##SUBST##|v|">|v|</a></td>
<td><a href="##SUBST##|v|">|v|</a></td>
<td></td>
<td colspan="2"></td>
<td colspan="2"></td>
<td><a href="##SUBST##|v|">|v|</a></td>
<td><a href="##SUBST##|v|">|v|</a></td>
<td><a href="##SUBST##|v|">|v|</a></td>
<td><a href="##SUBST##|v|">|v|</a></td>
</tr>
<tr>
<td><a href="./linux/flatpak.html">Flatpak</a></td>
<td></td>
<td></td>
<td></td>
<td colspan="2"></td>
<td colspan="2"></td>
<td><a href="##SUBST##|v|">|v|</a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
<td><a href="##SUBST##|v|">|v|</a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
</tr>
<tr>
<td><a
href="./linux/system.html"><strong>System package</strong></a></td>
<td><a href="##SUBST##|y|">|y|</a></td>
<td><a href="##SUBST##|y|">|y|</a></td>
<td></td>
<td colspan="2"></td>
<td colspan="2"></td>
<td><a href="##SUBST##|v|">|v|</a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
<td><a href="##SUBST##|v|">|v|</a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
</tr>
<tr>
<td rowspan="2">macOS</td>
<td><a href="./macOS/app.html"><strong>.app bundle</strong></a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
<td></td>
<td colspan="2"></td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td><a href="./macOS/xcode.html">Xcode project</a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
<td></td>
<td colspan="2"></td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>Web</td>
<td><a href="./web/static.html"><strong>Static</strong></a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
<td><a href="##SUBST##|v|">|v|</a></td>
<td colspan="2"><a href="##SUBST##|f|">|f|</a></td>
<td colspan="2"><a href="##SUBST##|v|">|v|</a></td>
<td><a href="##SUBST##|v|">|v|</a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
<td><a href="##SUBST##|v|">|v|</a></td>
<td><a href="##SUBST##|f|">|f|</a></td>
</tr>
<tr>
<td rowspan="2">Windows</td>
<td><a href="./windows/app.html"><strong>Windows app</strong></a></td>
<td></td>
<td></td>
<td></td>
<td colspan="2"><a href="##SUBST##|f|">|f|</a></td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td><a href="./windows/visualstudio.html">Visual Studio project</a></td>
<td></td>
<td></td>
<td></td>
<td colspan="2"><a href="##SUBST##|f|">|f|</a></td>
<td colspan="2"></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
</tbody>
</table>
