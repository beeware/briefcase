# Platform support { #platform-support-key }

|      {{ ci_tested }}      | Supported and tested in CI              |
|:-------------------------:|-----------------------------------------|
|  {{ maintainer_tested }}  | **Supported and tested by maintainers** |
|     {{ not_tested }}      | **Supported but not tested regularly**  |

<table class="platform-support-table">
<colgroup>
<col style="width: 7%" />
<col style="width: 35%" />
<col style="width: 8%" />
<col style="width: 7%" />
<col style="width: 8%" />
<col style="width: 1%" />
<col style="width: 5%" />
<col style="width: 5%" />
<col style="width: 3%" />
<col style="width: 7%" />
<col style="width: 7%" />
<col style="width: 8%" />
<col style="width: 7%" />
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
<td><a href="android/gradle"><strong>Gradle project</strong></a></td>
<td>{{ ci_tested }}</td>
<td>{{ ci_tested }}</td>
<td></td>
<td colspan="2">{{ ci_tested }}</td>
<td colspan="2"></td>
<td>{{ not_tested }}</td>
<td>{{ ci_tested }}</td>
<td>{{ not_tested }}</td>
<td>{{ not_tested }}</td>
</tr>
<tr>
<td>iOS</td>
<td><a href="./iOS/xcode"><strong>Xcode project</strong></a></td>
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
<tr>
<td rowspan="3">Linux</td>
<td><a href="./linux/appimage">AppImage</a></td>
<td>{{ not_tested }}</td>
<td>{{ not_tested }}</td>
<td></td>
<td colspan="2"></td>
<td colspan="2"></td>
<td>{{ not_tested }}</td>
<td>{{ not_tested }}</td>
<td>{{ not_tested }}</td>
<td>{{ not_tested }}</td>
</tr>
<tr>
<td><a href="./linux/flatpak">Flatpak</a></td>
<td class="tested-status-symbol"></td>
<td></td>
<td></td>
<td colspan="2"></td>
<td colspan="2"></td>
<td>{{ not_tested }}</td>
<td>{{ ci_tested }}</td>
<td>{{ not_tested }}</td>
<td>{{ ci_tested }}</td>
</tr>
<tr>
<td><a href="./linux/system"><strong>System package</strong></a></td>
<td class="tested-status-symbol">{{ maintainer_tested }}</td>
<td>{{ maintainer_tested }}</td>
<td></td>
<td colspan="2"></td>
<td colspan="2"></td>
<td>{{ not_tested }}</td>
<td>{{ ci_tested }}</td>
<td>{{ not_tested }}</td>
<td>{{ ci_tested }}</td>
</tr>
<tr>
<td rowspan="2">macOS</td>
<td><a href="./macOS/app"><strong>.app bundle</strong></a></td>
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
<tr>
<td><a href="./macOS/xcode/#"><span>Xcode project</span></a></td>
<td class="tested-status-symbol">{{ ci_tested }}</td>
<td>{{ ci_tested }}</td>
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
<td><a href="./web/static/#"><strong>Static</strong></a></td>
<td>{{ ci_tested }}</td>
<td>{{ ci_tested }}</td>
<td>{{ not_tested }}</td>
<td colspan="2">{{ ci_tested }}</td>
<td colspan="2">{{ not_tested }}</td>
<td>{{ not_tested }}</td>
<td>{{ ci_tested }}</td>
<td>{{ not_tested }}</td>
<td>{{ ci_tested }}</td>
</tr>
<tr>
<td class="target-app-format-windows" rowspan="2">Windows</td>
<td><a href="./windows/app"><strong>Windows app</strong></a></td>
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
<tr>
<td><a href="./windows/visualstudio"><span>Visual Studio project</span></a></td>
<td class="tested-status-symbol"></td>
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
