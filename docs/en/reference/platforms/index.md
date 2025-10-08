# Platform support {#platform-support-key}

|                       |                                     |
|-----------------------|-------------------------------------|
| [\|f\|](##SUBST##|f|) | Supported and tested in CI          |
| [\|y\|](##SUBST##|y|) | Supported and tested by maintainers |
| [\|v\|](##SUBST##|v|) | Supported but not tested regularly  |

| Target App | Format                |        |       |         | Host   | System |       |        |     |       |
|------------|-----------------------|--------|-------|---------|--------|--------|-------|--------|-----|-------|
|            |                       | macOS  |       | Windows |        |        | Linux |
|            |                       | x86‑64 | arm64 | x86     | x86‑64 | arm64  | x86   | x86‑64 | arm | arm64 |
| Android    | Gradle project        | f      | f     |         | f      |        | v     | f      | v   | v     |
| iOS        | Xcode project         | f      | f     |         |        |        |       |        |     |       |
| Linux      | AppImage              | v      | v     |         |        |        | v     | f      | v   | v     |
|            | Flatpak               |        |       |         |        |        | v     | f      | v   | f     |
|            | System package        | y      | y     |         |        |        | v     | f      | v   | f     |
| macOS      | .app bundle           | f      | f     |         |        |        |       |        |     |       |
|            | Xcode project         | f      | f     |         |        |        |       |        |     |       |
| Web        | Static                | f      | f     | v       | f      | v      | v     | f      | v   | f     |
| Windows    | Windows app           |        |       |         | f      |        |       |        |     |       |
|            | Visual Studio project |        |       |         | f      |        |       |        |     |       |
