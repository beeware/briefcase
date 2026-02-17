# Release History

<!-- towncrier release notes start -->

## 0.3.26 (2025-12-04)

### Features

* When a project specifies a dependency using a local file path, `briefcase dev` now installs that dependency in editable mode. This means changes in the local project will be immediately reflected in the development environment, without needing to reinstall the package. ([#2334](https://github.com/beeware/briefcase/issues/2334))
* The `build` and `run` commands for Windows, macOS and iOS now have a `--debug` option for integration with PDB and Visual Studio Code. ([#2147](https://github.com/beeware/briefcase/issues/2147), [#2352](https://github.com/beeware/briefcase/issues/2352))
* Windows MSI installers can now include post-install and pre-uninstall scripts, including selection of optional features as part of the install and uninstall process. ([#2191](https://github.com/beeware/briefcase/issues/2191), [#2573](https://github.com/beeware/briefcase/issues/2573))
* Windows MSI installers now display and ask for acceptance of the project's license as part of the install process. ([#2191](https://github.com/beeware/briefcase/issues/2191))
* Briefcase's web backend now gives full control of the PyScript and GUI toolkit configuration to the Python packages that are installed in the app. ([#2337](https://github.com/beeware/briefcase/issues/2337))
* `briefcase dev` no longer overwrites explicitly set environment variables. ([#2497](https://github.com/beeware/briefcase/issues/2497))
* Briefcase now has a cross-platform representation of Bluetooth permissions. ([#2522](https://github.com/beeware/briefcase/issues/2522))
* When packaging an app in MSI format, creation of Start menu shortcuts can now be disabled with the `install_launcher` setting. ([#2534](https://github.com/beeware/briefcase/issues/2534))
* Windows MSI installers now provide the option for users to configure the install directory for apps. ([#2553](https://github.com/beeware/briefcase/issues/2553))
* When a project defines multiple applications, `briefcase dev`and `briefcase run` now display an interactive menu allowing the user to select which application to start. ([#2574](https://github.com/beeware/briefcase/issues/2574))
* Briefcase now has the ability to manage virtual environments as part of a development environment. This feature is only used as part of the in-progress dev command for the web environment, but opens up opportunities for better environment isolation in the future. ([#2334](https://github.com/beeware/briefcase/issues/2334))

### Bugfixes

* The docs checks in `tox` now work if there are spaces in the path. ([#2477](https://github.com/beeware/briefcase/issues/2477))
* The system Python version check now works on Gentoo Linux. ([#2490](https://github.com/beeware/briefcase/issues/2490))
* Developer mode is now able to track the need to install requirements on a per-environment basis. ([#2495](https://github.com/beeware/briefcase/issues/2495))
* Permission disabling is now handled correctly ([#2522](https://github.com/beeware/briefcase/issues/2522))

### Backward Incompatible Changes

* Java JDK 17.0.17+10 is now used to package Android apps. Use `briefcase upgrade java` to update your Briefcase-installed JDK instance to this version. ([#2529](https://github.com/beeware/briefcase/issues/2529))

### Documentation

* Briefcase's documentation was migrated to Markdown format. ([#2502](https://github.com/beeware/briefcase/issues/2502))
* The obligations of a "well behaved" MSI-packaged application in ensuring a clean registry have been documented. ([#2554](https://github.com/beeware/briefcase/issues/2554))

### Misc

* [#2381](https://github.com/beeware/briefcase/issues/2381), [#2384](https://github.com/beeware/briefcase/issues/2384), [#2457](https://github.com/beeware/briefcase/issues/2457), [#2459](https://github.com/beeware/briefcase/issues/2459), [#2460](https://github.com/beeware/briefcase/issues/2460), [#2461](https://github.com/beeware/briefcase/issues/2461), [#2462](https://github.com/beeware/briefcase/issues/2462), [#2466](https://github.com/beeware/briefcase/issues/2466), [#2467](https://github.com/beeware/briefcase/issues/2467), [#2468](https://github.com/beeware/briefcase/issues/2468), [#2469](https://github.com/beeware/briefcase/issues/2469), [#2470](https://github.com/beeware/briefcase/issues/2470), [#2471](https://github.com/beeware/briefcase/issues/2471), [#2478](https://github.com/beeware/briefcase/issues/2478), [#2479](https://github.com/beeware/briefcase/issues/2479), [#2481](https://github.com/beeware/briefcase/issues/2481), [#2482](https://github.com/beeware/briefcase/issues/2482), [#2484](https://github.com/beeware/briefcase/issues/2484), [#2485](https://github.com/beeware/briefcase/issues/2485), [#2487](https://github.com/beeware/briefcase/issues/2487), [#2492](https://github.com/beeware/briefcase/issues/2492), [#2493](https://github.com/beeware/briefcase/issues/2493), [#2499](https://github.com/beeware/briefcase/issues/2499), [#2500](https://github.com/beeware/briefcase/issues/2500), [#2504](https://github.com/beeware/briefcase/issues/2504), [#2505](https://github.com/beeware/briefcase/issues/2505), [#2506](https://github.com/beeware/briefcase/issues/2506), [#2507](https://github.com/beeware/briefcase/issues/2507), [#2508](https://github.com/beeware/briefcase/issues/2508), [#2509](https://github.com/beeware/briefcase/issues/2509), [#2511](https://github.com/beeware/briefcase/issues/2511), [#2512](https://github.com/beeware/briefcase/issues/2512), [#2517](https://github.com/beeware/briefcase/issues/2517), [#2518](https://github.com/beeware/briefcase/issues/2518), [#2519](https://github.com/beeware/briefcase/issues/2519), [#2520](https://github.com/beeware/briefcase/issues/2520), [#2520](https://github.com/beeware/briefcase/issues/2520), [#2521](https://github.com/beeware/briefcase/issues/2521), [#2523](https://github.com/beeware/briefcase/issues/2523), [#2524](https://github.com/beeware/briefcase/issues/2524), [#2526](https://github.com/beeware/briefcase/issues/2526), [#2528](https://github.com/beeware/briefcase/issues/2528), [#2533](https://github.com/beeware/briefcase/issues/2533), [#2535](https://github.com/beeware/briefcase/issues/2535), [#2536](https://github.com/beeware/briefcase/issues/2536), [#2537](https://github.com/beeware/briefcase/issues/2537), [#2538](https://github.com/beeware/briefcase/issues/2538), [#2539](https://github.com/beeware/briefcase/issues/2539), [#2540](https://github.com/beeware/briefcase/issues/2540), [#2541](https://github.com/beeware/briefcase/issues/2541), [#2542](https://github.com/beeware/briefcase/issues/2542), [#2544](https://github.com/beeware/briefcase/issues/2544), [#2548](https://github.com/beeware/briefcase/issues/2548), [#2549](https://github.com/beeware/briefcase/issues/2549), [#2550](https://github.com/beeware/briefcase/issues/2550), [#2551](https://github.com/beeware/briefcase/issues/2551), [#2552](https://github.com/beeware/briefcase/issues/2552), [#2555](https://github.com/beeware/briefcase/issues/2555), [#2556](https://github.com/beeware/briefcase/issues/2556), [#2557](https://github.com/beeware/briefcase/issues/2557), [#2558](https://github.com/beeware/briefcase/issues/2558), [#2564](https://github.com/beeware/briefcase/issues/2564), [#2565](https://github.com/beeware/briefcase/issues/2565), [#2566](https://github.com/beeware/briefcase/issues/2566), [#2568](https://github.com/beeware/briefcase/issues/2568), [#2568](https://github.com/beeware/briefcase/issues/2568), [#2569](https://github.com/beeware/briefcase/issues/2569), [#2570](https://github.com/beeware/briefcase/issues/2570), [#2571](https://github.com/beeware/briefcase/issues/2571), [#2572](https://github.com/beeware/briefcase/issues/2572), [#2576](https://github.com/beeware/briefcase/issues/2576), [#2577](https://github.com/beeware/briefcase/issues/2577), [#2585](https://github.com/beeware/briefcase/issues/2585), [#2586](https://github.com/beeware/briefcase/issues/2586), [#2589](https://github.com/beeware/briefcase/issues/2589), [#2590](https://github.com/beeware/briefcase/issues/2590)

## 0.3.25 (2025-08-26)

### Features

- Android apps can now pass `--forward-port` and `--reverse-port` to connect ports in the emulated device to the host environment ([#2369](https://github.com/beeware/briefcase/issues/2369))
- Android applications now target Android SDK 35 by default. ([#2393](https://github.com/beeware/briefcase/issues/2393))
- Support for Python 3.14 has been added. ([#2431](https://github.com/beeware/briefcase/issues/2431))
- Windows apps and Visual Studio projects can now reference pre-release Python versions as a support revision. ([#2432](https://github.com/beeware/briefcase/issues/2432))
- If an iOS or macOS app doesn't specify a minimum OS version, the minimum OS version is now derived from the support package, rather than being hard coded. ([#2443](https://github.com/beeware/briefcase/issues/2443))

### Bugfixes

- Apps that contain file paths longer than 260 characters can now be included in MSI installers. ([#948](https://github.com/beeware/briefcase/issues/948))
- Windows builds now have improved hints when a virus checker interrupts a build. ([#1530](https://github.com/beeware/briefcase/issues/1530))
- Wheels that contain Linux `.so` files are now usable on macOS. ([#2429](https://github.com/beeware/briefcase/issues/2429))
- iOS and macOS apps now read the minimum supported OS version from the Python framework's metadata, rather than requiring a `VERSIONS` file as part of the support package. ([#2443](https://github.com/beeware/briefcase/issues/2443))

### Backward Incompatible Changes

- Support for Python 3.9 has been dropped. ([#2431](https://github.com/beeware/briefcase/issues/2431))

### Documentation

- Details on usage of iOS and Android third-party wheels have been updated to reflect recent changes in the Python packaging ecosystem. ([#2423](https://github.com/beeware/briefcase/issues/2423))

### Misc

- [#2334](https://github.com/beeware/briefcase/issues/2334), [#1650](https://github.com/beeware/briefcase/issues/1650), [#2364](https://github.com/beeware/briefcase/issues/2364), [#2378](https://github.com/beeware/briefcase/issues/2378), [#2379](https://github.com/beeware/briefcase/issues/2379), [#2381](https://github.com/beeware/briefcase/issues/2381), [#2389](https://github.com/beeware/briefcase/issues/2389), [#2394](https://github.com/beeware/briefcase/issues/2394), [#2402](https://github.com/beeware/briefcase/issues/2402), [#2406](https://github.com/beeware/briefcase/issues/2406), [#2407](https://github.com/beeware/briefcase/issues/2407), [#2408](https://github.com/beeware/briefcase/issues/2408), [#2411](https://github.com/beeware/briefcase/issues/2411), [#2413](https://github.com/beeware/briefcase/issues/2413), [#2415](https://github.com/beeware/briefcase/issues/2415), [#2416](https://github.com/beeware/briefcase/issues/2416), [#2417](https://github.com/beeware/briefcase/issues/2417), [#2422](https://github.com/beeware/briefcase/issues/2422), [#2425](https://github.com/beeware/briefcase/issues/2425), [#2427](https://github.com/beeware/briefcase/issues/2427), [#2434](https://github.com/beeware/briefcase/issues/2434), [#2436](https://github.com/beeware/briefcase/issues/2436), [#2438](https://github.com/beeware/briefcase/issues/2438), [#2439](https://github.com/beeware/briefcase/issues/2439), [#2440](https://github.com/beeware/briefcase/issues/2440), [#2441](https://github.com/beeware/briefcase/issues/2441), [#2445](https://github.com/beeware/briefcase/issues/2445), [#2446](https://github.com/beeware/briefcase/issues/2446), [#2447](https://github.com/beeware/briefcase/issues/2447), [#2448](https://github.com/beeware/briefcase/issues/2448), [#2449](https://github.com/beeware/briefcase/issues/2449), [#2452](https://github.com/beeware/briefcase/issues/2452), [#2453](https://github.com/beeware/briefcase/issues/2453), [#2454](https://github.com/beeware/briefcase/issues/2454), [#2455](https://github.com/beeware/briefcase/issues/2455)

## 0.3.24 (2025-07-10)

### Features

- When an iOS or macOS binary wheel cannot be found, the error message now provides more useful hints regarding the possible cause. ([#2230](https://github.com/beeware/briefcase/issues/2230))
- Document type and file associations have been improved on macOS. ([#2284](https://github.com/beeware/briefcase/issues/2284))
- Briefcase can now be used to sign, package and notarize apps that Briefcase didn't create. You can now use another tool to create a macOS, Windows or Linux application, and then use Briefcase to complete the process of turning that app into a signed and notarized release artefact. ([#2326](https://github.com/beeware/briefcase/issues/2326))

### Bugfixes

- A redundant signing phase has been removed when packaging an apps for macOS. ([#1099](https://github.com/beeware/briefcase/issues/1099))
- An error is now raised on macOS if Briefcase is used on an iCloud mounted drive. iCloud synchronization adds metadata to some folders, which is incompatible with the signing process. ([#1808](https://github.com/beeware/briefcase/issues/1808))
- An app's formal name can now include a `.` character. ([#2151](https://github.com/beeware/briefcase/issues/2151))
- Distribution-specific cumulative settings (such as `requires`) now correctly accumulate, rather than overwriting more general values. ([#2188](https://github.com/beeware/briefcase/issues/2188))
- Briefcase will now default to using the system certificate store when performing HTTPS downloads. ([#2296](https://github.com/beeware/briefcase/issues/2296))
- Briefcase now provides richer error information when it is unable to complete a download. In particular, issues associated with SSL verification are now reported as such, rather than as a generic "are you offline?" message. ([#2296](https://github.com/beeware/briefcase/issues/2296))
- The presence of a `PIP_REQUIRE_VIRTUALENV` environment marker no longer influences the operation of dependency installation on iOS. The iOS installation environments is inherently isolated, so this flag is redundant; but in some circumstances, it would prevent the installation of dependencies into a project. ([#2325](https://github.com/beeware/briefcase/issues/2325))

### Backward Incompatible Changes

- Briefcase now uses WiX version 5.0.2 to generate MSI installers on Windows. Any Windows apps created with previous versions of Briefcase will need to be re-generated by running `briefcase create`. ([#1185](https://github.com/beeware/briefcase/issues/1185))

### Documentation

- Documentation about deploying to physical iOS devices has been added. ([#1190](https://github.com/beeware/briefcase/issues/1190))
- References to Briefcase's settings are now hyperlinked for ease of cross-referencing. ([#2341](https://github.com/beeware/briefcase/issues/2341))
- A guide for publishing apps to the macOS App Store has been added. ([#2360](https://github.com/beeware/briefcase/issues/2360))
- Briefcase's documentation now uses a header and style consistent with the BeeWare website. ([#2375](https://github.com/beeware/briefcase/issues/2375))

### Misc

- [#1669](https://github.com/beeware/briefcase/issues/1669), [#1696](https://github.com/beeware/briefcase/issues/1696), [#2280](https://github.com/beeware/briefcase/issues/2280), [#2281](https://github.com/beeware/briefcase/issues/2281), [#2287](https://github.com/beeware/briefcase/issues/2287), [#2288](https://github.com/beeware/briefcase/issues/2288), [#2289](https://github.com/beeware/briefcase/issues/2289), [#2291](https://github.com/beeware/briefcase/issues/2291), [#2292](https://github.com/beeware/briefcase/issues/2292), [#2295](https://github.com/beeware/briefcase/issues/2295), [#2310](https://github.com/beeware/briefcase/issues/2310), [#2311](https://github.com/beeware/briefcase/issues/2311), [#2312](https://github.com/beeware/briefcase/issues/2312), [#2313](https://github.com/beeware/briefcase/issues/2313), [#2319](https://github.com/beeware/briefcase/issues/2319), [#2320](https://github.com/beeware/briefcase/issues/2320), [#2321](https://github.com/beeware/briefcase/issues/2321), [#2322](https://github.com/beeware/briefcase/issues/2322), [#2323](https://github.com/beeware/briefcase/issues/2323), [#2324](https://github.com/beeware/briefcase/issues/2324), [#2327](https://github.com/beeware/briefcase/issues/2327), [#2330](https://github.com/beeware/briefcase/issues/2330), [#2331](https://github.com/beeware/briefcase/issues/2331), [#2335](https://github.com/beeware/briefcase/issues/2335), [#2339](https://github.com/beeware/briefcase/issues/2339), [#2343](https://github.com/beeware/briefcase/issues/2343), [#2343](https://github.com/beeware/briefcase/issues/2343), [#2345](https://github.com/beeware/briefcase/issues/2345), [#2346](https://github.com/beeware/briefcase/issues/2346), [#2347](https://github.com/beeware/briefcase/issues/2347), [#2349](https://github.com/beeware/briefcase/issues/2349), [#2358](https://github.com/beeware/briefcase/issues/2358), [#2359](https://github.com/beeware/briefcase/issues/2359), [#2361](https://github.com/beeware/briefcase/issues/2361), [#2362](https://github.com/beeware/briefcase/issues/2362), [#2367](https://github.com/beeware/briefcase/issues/2367), [#2371](https://github.com/beeware/briefcase/issues/2371), [#2372](https://github.com/beeware/briefcase/issues/2372), [#2373](https://github.com/beeware/briefcase/issues/2373), [#2374](https://github.com/beeware/briefcase/issues/2374), [#2380](https://github.com/beeware/briefcase/issues/2380), [#2385](https://github.com/beeware/briefcase/issues/2385), [#2386](https://github.com/beeware/briefcase/issues/2386)

## 0.3.23 (2025-05-08)

### Features

- Cookiecutter filters for escaping XML content and attributes have been added. ([#2103](https://github.com/beeware/briefcase/issues/2103))
- Briefcase now supports the use of `HISTORY`, `NEWS` and `RELEASES` as filenames for the change log of a project (in addition to `CHANGELOG`). It also supports the use of `.md`, `.rst` and `.txt` extensions on those files. ([#2116](https://github.com/beeware/briefcase/issues/2116))
- It is now possible to ask Boolean question using the Console Interface. ([#2128](https://github.com/beeware/briefcase/issues/2128))
- The `create`, `build`, `package` and `update` commands can now be run on a single app within a multi-app project by using the `-a` / `--app` option. ([#2148](https://github.com/beeware/briefcase/issues/2148))
- The Toga app bootstrap now generates apps that use Toga 0.5. ([#2193](https://github.com/beeware/briefcase/issues/2193))
- An app can now enforce a minimum supported OS version by defining a `min_os_version` configuration item on a per-platform basis. This minimum value will be used on macOS, iOS and Android deployments. ([#2233](https://github.com/beeware/briefcase/issues/2233))
- The Flatpak runtimes for new projects were updated. `org.gnome.Platform` will now default to 47; and `org.kde.Platform` will now default to 6.9. ([#2258](https://github.com/beeware/briefcase/issues/2258))
- Android packages are now built using version 19.0 of Android's Command-line Tools; this version will be automatically installed at first use. ([#2260](https://github.com/beeware/briefcase/issues/2260))
- When creating a new project with `briefcase new`, or converting an existing project with `briefcase convert`, Briefcase will now try to infer the author's name and email address from the git configuration. ([#2269](https://github.com/beeware/briefcase/issues/2269))

### Bugfixes

- `.pth` files created by packages installed as dependencies are now correctly processed during application startup on macOS, Windows, Linux and iOS. ([#381](https://github.com/beeware/briefcase/issues/381))
- Error handling during JDK upgrades has been improved. ([#1520](https://github.com/beeware/briefcase/issues/1520))
- The iOS log filter was improved to hide an message about `getpwuid_r` that can be ignored. ([#2163](https://github.com/beeware/briefcase/issues/2163))
- New apps using Toga on Linux will impose an upper version pin on PyGObject, limiting that package to `< 3.52.1`. This is required to ensure that older Debian-based distributions are supported by default. This pin can be removed if these support for these distributions is not required, as long as some additional changes are made to the `system_requires` and `system_runtime_requires` definitions. The required changes are included (commented out) as part of the new project template. ([#2190](https://github.com/beeware/briefcase/issues/2190))
- License names now follow the [SPDX License List](https://spdx.org/licenses/). ([#2270](https://github.com/beeware/briefcase/issues/2270))

### Backward Incompatible Changes

- Briefcase can no longer install pure Python macOS packages from a source archive (i.e., a `.tar.gz` file published on PyPI). If a package is pure Python, it *must* be provided as a `py3-none-any` wheel. Briefcase's [macOS platform documentation](https://briefcase.beeware.org/en/latest/reference/platforms/macOS) contains details on how to provide a `py3-none-any` wheel when PyPI does not provide one. ([#2163](https://github.com/beeware/briefcase/issues/2163))
- The `app_packages` folder now occurs *after* the `app` folder in the package resolution path on Windows, Linux, macOS and iOS. This will result in subtle changes in behavior if you have packages defined in your `sources` that have the same name as packages installed from your `requires`. ([#2204](https://github.com/beeware/briefcase/issues/2204))
- The iOS app template no longer uses the `iphoneos_deployment_target` setting to configure the minimum OS version. This variable was undocumented; you should modify any usage of this variable to the newly added (and documented) `min_os_version` setting. ([#2233](https://github.com/beeware/briefcase/issues/2233))
- If you have a PySide6 app deployed to macOS, you must add `min_os_version = "12.0"` to your macOS project configuration. As of PySide 6.8.0, PySide6 macOS wheels are tagged with a minimum supported macOS version of 12.0. Previously, Briefcase would install the macOS 12 wheel, but the Briefcase app would declare itself as supporting macOS 11. This would cause errors if the app was run on macOS 11. Briefcase will no longer install macOS wheels that are incompatible with the minimum OS version declared by the app (11.0 by default). The additional `min_os_version` configuration option is now required to allow Briefcase to resolve the installation of PySide6 wheels. ([#2240](https://github.com/beeware/briefcase/issues/2240))
- Java JDK 17.0.15+6 is now used to package Android apps. Use `briefcase upgrade java` to update your Briefcase-installed JDK instance to this version. ([#2259](https://github.com/beeware/briefcase/issues/2259))
- The `new` command now uses [SPDX identifiers](https://spdx.org/licenses/) when referring to licenses. If you have been using the `-Q license=XXX` option to automate application creation, you will need to modify the value provided to match the SPDX specifier for that license (e.g., `MIT` instead of `MIT license`, and `BSD-3-Clause` instead of `BSD`). ([#2270](https://github.com/beeware/briefcase/issues/2270))

### Documentation

- A how to guide for command-line apps was added. ([#1947](https://github.com/beeware/briefcase/issues/1947))
- Platform notes were added on removing static binary content from iOS and macOS apps. ([#2161](https://github.com/beeware/briefcase/issues/2161))
- The macOS and Windows platform documentation has been simplified to remove duplication of content between output formats. ([#2162](https://github.com/beeware/briefcase/issues/2162))

### Misc

- [#1696](https://github.com/beeware/briefcase/issues/1696), [#2153](https://github.com/beeware/briefcase/issues/2153), [#2155](https://github.com/beeware/briefcase/issues/2155), [#2158](https://github.com/beeware/briefcase/issues/2158), [#2159](https://github.com/beeware/briefcase/issues/2159), [#2160](https://github.com/beeware/briefcase/issues/2160), [#2168](https://github.com/beeware/briefcase/issues/2168), [#2169](https://github.com/beeware/briefcase/issues/2169), [#2170](https://github.com/beeware/briefcase/issues/2170), [#2171](https://github.com/beeware/briefcase/issues/2171), [#2172](https://github.com/beeware/briefcase/issues/2172), [#2174](https://github.com/beeware/briefcase/issues/2174), [#2175](https://github.com/beeware/briefcase/issues/2175), [#2176](https://github.com/beeware/briefcase/issues/2176), [#2177](https://github.com/beeware/briefcase/issues/2177), [#2178](https://github.com/beeware/briefcase/issues/2178), [#2179](https://github.com/beeware/briefcase/issues/2179), [#2184](https://github.com/beeware/briefcase/issues/2184), [#2185](https://github.com/beeware/briefcase/issues/2185), [#2186](https://github.com/beeware/briefcase/issues/2186), [#2196](https://github.com/beeware/briefcase/issues/2196), [#2205](https://github.com/beeware/briefcase/issues/2205), [#2206](https://github.com/beeware/briefcase/issues/2206), [#2207](https://github.com/beeware/briefcase/issues/2207), [#2208](https://github.com/beeware/briefcase/issues/2208), [#2209](https://github.com/beeware/briefcase/issues/2209), [#2210](https://github.com/beeware/briefcase/issues/2210), [#2215](https://github.com/beeware/briefcase/issues/2215), [#2217](https://github.com/beeware/briefcase/issues/2217), [#2218](https://github.com/beeware/briefcase/issues/2218), [#2219](https://github.com/beeware/briefcase/issues/2219), [#2220](https://github.com/beeware/briefcase/issues/2220), [#2221](https://github.com/beeware/briefcase/issues/2221), [#2222](https://github.com/beeware/briefcase/issues/2222), [#2223](https://github.com/beeware/briefcase/issues/2223), [#2237](https://github.com/beeware/briefcase/issues/2237), [#2247](https://github.com/beeware/briefcase/issues/2247), [#2248](https://github.com/beeware/briefcase/issues/2248), [#2249](https://github.com/beeware/briefcase/issues/2249), [#2262](https://github.com/beeware/briefcase/issues/2262), [#2263](https://github.com/beeware/briefcase/issues/2263), [#2264](https://github.com/beeware/briefcase/issues/2264), [#2265](https://github.com/beeware/briefcase/issues/2265), [#2266](https://github.com/beeware/briefcase/issues/2266), [#2267](https://github.com/beeware/briefcase/issues/2267), [#2276](https://github.com/beeware/briefcase/issues/2276), [#2277](https://github.com/beeware/briefcase/issues/2277), [#2278](https://github.com/beeware/briefcase/issues/2278)

## 0.3.22 (2025-02-07)

### Bugfixes

- Some error messages that are an expected part of the macOS notarization process are now hidden from default verbosity. ([#2149](https://github.com/beeware/briefcase/issues/2149))
- Briefcase no longer uses the `--no-python-version-warning` option when invoking pip. This option has been deprecated, is currently a no-op, and will be removed soon. ([#2149](https://github.com/beeware/briefcase/issues/2149))

### Backward Incompatible Changes

- Java JDK 17.0.14+7 is now used to package Android apps. Use `briefcase upgrade java` to update your Briefcase-installed JDK instance to this version. ([#2133](https://github.com/beeware/briefcase/issues/2133))

### Misc

- [#2136](https://github.com/beeware/briefcase/issues/2136), [#2137](https://github.com/beeware/briefcase/issues/2137), [#2138](https://github.com/beeware/briefcase/issues/2138), [#2141](https://github.com/beeware/briefcase/issues/2141), [#2142](https://github.com/beeware/briefcase/issues/2142), [#2143](https://github.com/beeware/briefcase/issues/2143), [#2144](https://github.com/beeware/briefcase/issues/2144), [#2145](https://github.com/beeware/briefcase/issues/2145)

## 0.3.21 (2025-01-24)

### Features

- Briefcase will now surface git's error messages if an error occurs when cloning a template repository. ([#1118](https://github.com/beeware/briefcase/issues/1118))
- Briefcase now supports per-app configuration of `pip install` command line arguments using `requirement_installer_args`. ([#1270](https://github.com/beeware/briefcase/issues/1270))
- If macOS app notarization is interrupted, the notarization attempt can now be resumed. ([#1472](https://github.com/beeware/briefcase/issues/1472))
- When a macOS notarization attempt fails, Briefcase now displays the cause of the notarization failure. ([#1472](https://github.com/beeware/briefcase/issues/1472))
- When an existing project uses the `convert` wizard to add a Briefcase configuration, the updated `pyproject.toml` now includes a stub configuration for all platforms. ([#1899](https://github.com/beeware/briefcase/issues/1899))
- The `briefcase convert` command can now be used to configure a console-based applications. ([#1900](https://github.com/beeware/briefcase/issues/1900))
- If Briefcase receives an error invoking a system tool, it will now surface the raw error message to the user in addition to logging the error. ([#1907](https://github.com/beeware/briefcase/issues/1907))
- The project wizard now generates a more complete configuration file when no GUI framework is selected. ([#2006](https://github.com/beeware/briefcase/issues/2006))
- The web template now targets PyScript version 2024.11.1. In addition, the web template can provide a base `pyscript.toml` that Briefcase will update as required during the build process. ([#2080](https://github.com/beeware/briefcase/issues/2080))
- Briefcase now uses native pip handling for iOS installs. ([#2101](https://github.com/beeware/briefcase/issues/2101))
- When a verbosity level of 3 (i.e., `-vvv`) is selected, any tasks that would normally be performed in parallel will now be performed serially. ([#2110](https://github.com/beeware/briefcase/issues/2110))
- Linux on arm64 is now a fully supported platform. ([#2113](https://github.com/beeware/briefcase/issues/2113))
- Project bootstraps now have access to the Briefcase console and the overrides specified with `-Q` options at the command line. ([#2114](https://github.com/beeware/briefcase/issues/2114))
- Project bootstraps can now define a `post_generate()` extension point. This will be invoked after the new project template has been generated, providing a way for bootstraps to add additional files to the generated project. ([#2119](https://github.com/beeware/briefcase/issues/2119))

### Bugfixes

- Briefcase now uses `ditto` to archive apps for submission to the notarization service, rather than standard `zip` tooling. This ensures that UTF-8 encoding and file system resources are preserved. ([#1218](https://github.com/beeware/briefcase/issues/1218))
- The Gradle file generated for Android projects now correctly escapes single quotes. ([#1876](https://github.com/beeware/briefcase/issues/1876))
- Pre-release Python interpreter versions are no longer rejected as matching candidates in PEP 621 `requires-python` checks. ([#2034](https://github.com/beeware/briefcase/issues/2034))
- Briefcase no longer fails to create projects or builds because it cannot update the Git configuration for the relevant template. ([#2077](https://github.com/beeware/briefcase/issues/2077))
- Support packages for Linux Flatpak and AppImage builds are now downloaded from the `astral-sh` repository, rather than the `indygreg` repository. This reflect the recent transfer of ownership of the project. ([#2087](https://github.com/beeware/briefcase/issues/2087))
- A Debian-based system that does *not* have `build-essential` installed, but *does* have the constituent packages of `build-essential` installed, can now build Briefcase system packages. ([#2096](https://github.com/beeware/briefcase/issues/2096))
- The arguments passed to `xcodebuild` when compiling an iOS app have been modified to avoid a warning about an ignored argument. ([#2102](https://github.com/beeware/briefcase/issues/2102))
- The hints displayed to the user when an identity has been selected now more accurately reflect the context in which they have been invoked. ([#2110](https://github.com/beeware/briefcase/issues/2110))

### Backward Incompatible Changes

- Flatpak apps no longer request D-Bus session access by default. Most apps have no need to access the D-Bus session, unless they're a development tool that is inspecting D-Bus messages at runtime. If you experience errors related to this change, it is likely caused by an inconsistency between the `bundle` definition in your app configuration, and the way the app describes its bundle ID at runtime. If you *do* require D-Bus access, adding `finish_arg."socket=session-bus" = true` to the Flatpak configuration for your app will restore D-Bus session access. ([#2074](https://github.com/beeware/briefcase/issues/2074))
- Briefcase can no longer install pure Python iOS packages from a source archive (i.e., a `.tar.gz` file published on PyPI). If a package is pure Python, it *must* be provided as a `py3-none-any` wheel. Briefcase's [iOS platform documentation](https://briefcase.beeware.org/en/latest/reference/platforms/iOS/xcode#requirements-cannot-be-provided-as-source-tarballs) contains details on how to provide a `py3-none-any` wheel when PyPI does not provide one. ([#2101](https://github.com/beeware/briefcase/issues/2101))
- The API for project bootstraps has been slightly modified. The constructor for a bootstrap must now accept a console argument; the `extra_context()` method must now accept a `project_overrides` argument. ([#2114](https://github.com/beeware/briefcase/issues/2114))

### Misc

- [#2032](https://github.com/beeware/briefcase/issues/2032), [#2039](https://github.com/beeware/briefcase/issues/2039), [#2043](https://github.com/beeware/briefcase/issues/2043), [#2044](https://github.com/beeware/briefcase/issues/2044), [#2048](https://github.com/beeware/briefcase/issues/2048), [#2049](https://github.com/beeware/briefcase/issues/2049), [#2050](https://github.com/beeware/briefcase/issues/2050), [#2051](https://github.com/beeware/briefcase/issues/2051), [#2052](https://github.com/beeware/briefcase/issues/2052), [#2056](https://github.com/beeware/briefcase/issues/2056), [#2061](https://github.com/beeware/briefcase/issues/2061), [#2062](https://github.com/beeware/briefcase/issues/2062), [#2065](https://github.com/beeware/briefcase/issues/2065), [#2066](https://github.com/beeware/briefcase/issues/2066), [#2072](https://github.com/beeware/briefcase/issues/2072), [#2079](https://github.com/beeware/briefcase/issues/2079), [#2091](https://github.com/beeware/briefcase/issues/2091), [#2092](https://github.com/beeware/briefcase/issues/2092), [#2093](https://github.com/beeware/briefcase/issues/2093), [#2095](https://github.com/beeware/briefcase/issues/2095), [#2100](https://github.com/beeware/briefcase/issues/2100), [#2106](https://github.com/beeware/briefcase/issues/2106), [#2107](https://github.com/beeware/briefcase/issues/2107), [#2108](https://github.com/beeware/briefcase/issues/2108), [#2115](https://github.com/beeware/briefcase/issues/2115), [#2124](https://github.com/beeware/briefcase/issues/2124), [#2126](https://github.com/beeware/briefcase/issues/2126)

## 0.3.20 (2024-10-15)

### Features

- Support for Python 3.13 has been added.
- When the available version of Git is older than v2.17.0, an error message now prompts the user to upgrade their install of Git to proceed. ([#1915](https://github.com/beeware/briefcase/issues/1915))
- Apps packaged for Flatpak and AppImage now use a stripped (and smaller) Python support package. ([#1929](https://github.com/beeware/briefcase/issues/1929))
- macOS app templates can now specify what part of the support package should be copied into the final application bundle. ([#1933](https://github.com/beeware/briefcase/issues/1933))
- The Flatpak runtimes for new projects were updated. `org.freedesktop.Platform` will now default to 24.08; `org.gnome.Platform` will now default to 46; and `org.kde.Platform` will now default to 6.7. ([#1987](https://github.com/beeware/briefcase/issues/1987))
- Briefcase will now validate that the running Python interpreter meets requirements specified by the PEP 621 `requires-python` setting. If `requires-python` is not set, there is no change in behavior. Briefcase will also validate that `requires-python` is a valid version specifier as laid out by PEP 621's requirements. ([#2016](https://github.com/beeware/briefcase/issues/2016))

### Bugfixes

- Document type declarations are now fully validated. ([#1846](https://github.com/beeware/briefcase/issues/1846))
- The order in which nested frameworks and apps are signed on macOS has been corrected. ([#1891](https://github.com/beeware/briefcase/issues/1891))
- The spacing after the New Project wizard prompts are now consistent. ([#1896](https://github.com/beeware/briefcase/issues/1896))
- The documentation link provided when an app doesn't specify Gradle dependencies in its configuration has been corrected. ([#1905](https://github.com/beeware/briefcase/issues/1905))
- The log filter for iOS has been modified to capture logs generated when using PEP 730-style binary modules. ([#1933](https://github.com/beeware/briefcase/issues/1933))
- Briefcase is now able to remove symbolic links to directories as part of the template cleanup. ([#1933](https://github.com/beeware/briefcase/issues/1933))
- If a macOS support package contains symbolic links, those symbolic links will be preserved when the support package is copied into the app bundle. ([#1933](https://github.com/beeware/briefcase/issues/1933))
- Briefcase will no longer attempt to sign symbolic links in macOS apps. ([#1933](https://github.com/beeware/briefcase/issues/1933))
- Packages that include `.dist-info` content in vendored dependencies are now ignored as part of the binary widening process on macOS. If a binary package has vendored sub-packages, it is assumed that the top-level package includes the vendored packages' files in its wheel manifest. ([#1970](https://github.com/beeware/briefcase/issues/1970))
- The types used by `AppContext` in GUI toolkit bootstraps for creating new projects have been corrected. ([#1988](https://github.com/beeware/briefcase/issues/1988))
- The `--test` flag now works for console apps for macOS. ([#1992](https://github.com/beeware/briefcase/issues/1992))
- Python 3.12.7 introduced an incompatibility with the handling of `-C`, `-d` and other flags that accept values. This incompatibility has been corrected. ([#2026](https://github.com/beeware/briefcase/issues/2026))

### Backward Incompatible Changes

- Java JDK 17.0.12+7 is now used to package Android apps. Use `briefcase upgrade java` to update your Briefcase-installed JDK instance to this version. ([#1920](https://github.com/beeware/briefcase/issues/1920))
- Support for Python 3.8 has been dropped. ([#1934](https://github.com/beeware/briefcase/issues/1934))
- macOS and iOS templates have both had an epoch increase. macOS and iOS projects created with previous versions of Briefcase will need to be re-generated. ([#1934](https://github.com/beeware/briefcase/issues/1934))
- Any project using binary modules on iOS will need to be recompiled to use the binary linking format and wheel tag specified by [PEP 730](https://peps.python.org/pep-0730/) ([#1934](https://github.com/beeware/briefcase/issues/1934))

### Documentation

- A how-to guide for building apps in GitHub Actions CI was added. ([#400](https://github.com/beeware/briefcase/issues/400))
- Fixed error in example in briefcase run documentation. ([#1928](https://github.com/beeware/briefcase/issues/1928))
- Building Briefcase's documentation now requires the use of Python 3.12. ([#1942](https://github.com/beeware/briefcase/issues/1942))

### Misc

- [#1877](https://github.com/beeware/briefcase/issues/1877), [#1878](https://github.com/beeware/briefcase/issues/1878), [#1884](https://github.com/beeware/briefcase/issues/1884), [#1885](https://github.com/beeware/briefcase/issues/1885), [#1886](https://github.com/beeware/briefcase/issues/1886), [#1892](https://github.com/beeware/briefcase/issues/1892), [#1901](https://github.com/beeware/briefcase/issues/1901), [#1902](https://github.com/beeware/briefcase/issues/1902), [#1903](https://github.com/beeware/briefcase/issues/1903), [#1904](https://github.com/beeware/briefcase/issues/1904), [#1911](https://github.com/beeware/briefcase/issues/1911), [#1912](https://github.com/beeware/briefcase/issues/1912), [#1913](https://github.com/beeware/briefcase/issues/1913), [#1923](https://github.com/beeware/briefcase/issues/1923), [#1924](https://github.com/beeware/briefcase/issues/1924), [#1925](https://github.com/beeware/briefcase/issues/1925), [#1926](https://github.com/beeware/briefcase/issues/1926), [#1931](https://github.com/beeware/briefcase/issues/1931), [#1932](https://github.com/beeware/briefcase/issues/1932), [#1936](https://github.com/beeware/briefcase/issues/1936), [#1937](https://github.com/beeware/briefcase/issues/1937), [#1938](https://github.com/beeware/briefcase/issues/1938), [#1939](https://github.com/beeware/briefcase/issues/1939), [#1940](https://github.com/beeware/briefcase/issues/1940), [#1951](https://github.com/beeware/briefcase/issues/1951), [#1952](https://github.com/beeware/briefcase/issues/1952), [#1953](https://github.com/beeware/briefcase/issues/1953), [#1954](https://github.com/beeware/briefcase/issues/1954), [#1955](https://github.com/beeware/briefcase/issues/1955), [#1967](https://github.com/beeware/briefcase/issues/1967), [#1971](https://github.com/beeware/briefcase/issues/1971), [#1977](https://github.com/beeware/briefcase/issues/1977), [#1978](https://github.com/beeware/briefcase/issues/1978), [#1979](https://github.com/beeware/briefcase/issues/1979), [#1983](https://github.com/beeware/briefcase/issues/1983), [#1984](https://github.com/beeware/briefcase/issues/1984), [#1985](https://github.com/beeware/briefcase/issues/1985), [#1989](https://github.com/beeware/briefcase/issues/1989), [#1990](https://github.com/beeware/briefcase/issues/1990), [#1991](https://github.com/beeware/briefcase/issues/1991), [#1994](https://github.com/beeware/briefcase/issues/1994), [#1995](https://github.com/beeware/briefcase/issues/1995), [#2001](https://github.com/beeware/briefcase/issues/2001), [#2002](https://github.com/beeware/briefcase/issues/2002), [#2003](https://github.com/beeware/briefcase/issues/2003), [#2009](https://github.com/beeware/briefcase/issues/2009), [#2012](https://github.com/beeware/briefcase/issues/2012), [#2013](https://github.com/beeware/briefcase/issues/2013), [#2014](https://github.com/beeware/briefcase/issues/2014), [#2015](https://github.com/beeware/briefcase/issues/2015), [#2017](https://github.com/beeware/briefcase/issues/2017), [#2020](https://github.com/beeware/briefcase/issues/2020), [#2021](https://github.com/beeware/briefcase/issues/2021), [#2022](https://github.com/beeware/briefcase/issues/2022), [#2023](https://github.com/beeware/briefcase/issues/2023), [#2024](https://github.com/beeware/briefcase/issues/2024), [#2025](https://github.com/beeware/briefcase/issues/2025), [#2031](https://github.com/beeware/briefcase/issues/2031)

## 0.3.19 (2024-06-12)

### Features

- Briefcase can now package command line apps. ([#556](https://github.com/beeware/briefcase/issues/556))
- Templates that use pre-compiled stub binaries can now manage that artefact as an independent resource, rather than needing to include the binary in the template repository. This significantly reduces the size of the macOS and Windows app templates. ([#933](https://github.com/beeware/briefcase/issues/933))
- Template repositories are now fetched as blobless partial Git clones, reducing the size of initial downloads. ([#933](https://github.com/beeware/briefcase/issues/933))
- macOS now supports the generation of `.pkg` installers as a packaging format. ([#1184](https://github.com/beeware/briefcase/issues/1184))
- Android SDK Command Line Tools 12.0 is now used to build Android apps. ([#1778](https://github.com/beeware/briefcase/issues/1778))
- The new project wizard now includes links to known third-party GUI bootstraps. ([#1807](https://github.com/beeware/briefcase/issues/1807))
- The name of the license file can now be specified using a PEP 621-compliant format for the `license` setting. ([#1812](https://github.com/beeware/briefcase/issues/1812))
- The default Gradle dependencies for a Toga project no longer includes `SwipeRefreshLayout`. ([#1845](https://github.com/beeware/briefcase/issues/1845))

### Bugfixes

- Validation rules for bundle identifiers have been loosened. App IDs that contain country codes or language reserved words are no longer flagged as invalid. ([#1212](https://github.com/beeware/briefcase/issues/1212))
- macOS code signing no longer uses the deprecated "deep signing" option. ([#1221](https://github.com/beeware/briefcase/issues/1221))
- If `run` is executed directly after a `create` when using an `app` template on macOS or Windows, the implied `build` step is now correctly identified. ([#1729](https://github.com/beeware/briefcase/issues/1729))
- Escaping of quotation marks in TOML templates was corrected. ([#1746](https://github.com/beeware/briefcase/issues/1746))
- The Docker version on OpenSUSE Tumbleweed is now accepted and no longer triggers a warning message. ([#1773](https://github.com/beeware/briefcase/issues/1773))
- The formal name of an app is now validated. ([#1810](https://github.com/beeware/briefcase/issues/1810))
- macOS apps now generate `info.plist` entries for camera, photo library and microphone permissions. ([#1820](https://github.com/beeware/briefcase/issues/1820))

### Backward Incompatible Changes

- Briefcase now uses a private cache of Cookiecutter templates, rather than the shared `~/.cookiecutters` directory. You can reclaim disk space by deleting `~/.cookiecutters/briefcase-*` and `~/.cookiecutter_replay/briefcase-*` (or the entire `~/.cookiecutters` and `~/.cookiecutter_replay` folders if you are not using Cookiecutter for any other purposes). ([#933](https://github.com/beeware/briefcase/issues/933))
- The macOS `app` packaging format has been renamed `zip` for consistency with Windows, and to reflect the format of the output artefact. ([#1781](https://github.com/beeware/briefcase/issues/1781))
- The format for the `license` field has been converted to PEP 621 format. Existing projects that specify `license` as a string should update their configurations to point at the generated license file using `license.file = "LICENSE"`. ([#1812](https://github.com/beeware/briefcase/issues/1812))
- The PursuedPyBear bootstrap has been migrated to be part of the PursuedPyBear project. ([#1834](https://github.com/beeware/briefcase/issues/1834))

### Documentation

- Documentation describing manual signing requirement for Android packages has been added. ([#1703](https://github.com/beeware/briefcase/issues/1703))
- Documentation of Briefcase's support for document types has been improved. ([#1771](https://github.com/beeware/briefcase/issues/1771))
- Documentation on Briefcase's plug-in interfaces was added. ([#1807](https://github.com/beeware/briefcase/issues/1807))
- Documentation on the use of passwords in Android publication now encourages users to set non-default passwords. ([#1816](https://github.com/beeware/briefcase/issues/1816))

### Misc

- [#1184](https://github.com/beeware/briefcase/issues/1184), [#1472](https://github.com/beeware/briefcase/issues/1472), [#1777](https://github.com/beeware/briefcase/issues/1777), [#1784](https://github.com/beeware/briefcase/issues/1784), [#1786](https://github.com/beeware/briefcase/issues/1786), [#1789](https://github.com/beeware/briefcase/issues/1789), [#1790](https://github.com/beeware/briefcase/issues/1790), [#1791](https://github.com/beeware/briefcase/issues/1791), [#1792](https://github.com/beeware/briefcase/issues/1792), [#1793](https://github.com/beeware/briefcase/issues/1793), [#1798](https://github.com/beeware/briefcase/issues/1798), [#1799](https://github.com/beeware/briefcase/issues/1799), [#1800](https://github.com/beeware/briefcase/issues/1800), [#1817](https://github.com/beeware/briefcase/issues/1817), [#1819](https://github.com/beeware/briefcase/issues/1819), [#1821](https://github.com/beeware/briefcase/issues/1821), [#1823](https://github.com/beeware/briefcase/issues/1823), [#1839](https://github.com/beeware/briefcase/issues/1839), [#1840](https://github.com/beeware/briefcase/issues/1840), [#1841](https://github.com/beeware/briefcase/issues/1841), [#1842](https://github.com/beeware/briefcase/issues/1842), [#1843](https://github.com/beeware/briefcase/issues/1843), [#1847](https://github.com/beeware/briefcase/issues/1847), [#1850](https://github.com/beeware/briefcase/issues/1850), [#1851](https://github.com/beeware/briefcase/issues/1851), [#1853](https://github.com/beeware/briefcase/issues/1853), [#1857](https://github.com/beeware/briefcase/issues/1857), [#1860](https://github.com/beeware/briefcase/issues/1860), [#1863](https://github.com/beeware/briefcase/issues/1863), [#1867](https://github.com/beeware/briefcase/issues/1867), [#1869](https://github.com/beeware/briefcase/issues/1869), [#1871](https://github.com/beeware/briefcase/issues/1871), [#1872](https://github.com/beeware/briefcase/issues/1872), [#1873](https://github.com/beeware/briefcase/issues/1873), [#1874](https://github.com/beeware/briefcase/issues/1874)

## 0.3.18 (2024-05-06)

### Features

- Existing projects with a `pyproject.toml` configuration can now be converted into Briefcase apps using the `briefcase convert` command. ([#1202](https://github.com/beeware/briefcase/issues/1202))
- Apps packaged as AppImages are no longer dependent on `libcrypt.so.1`. ([#1383](https://github.com/beeware/briefcase/issues/1383))
- The `briefcase run` command now supports the `--target` option to run Linux apps from within Docker for other distributions. ([#1603](https://github.com/beeware/briefcase/issues/1603))
- The hints and recommendations that Docker prints in the console are now silenced. ([#1635](https://github.com/beeware/briefcase/issues/1635))
- In non-interactive environments, such as CI, a message is now printed to signify a task has begun where an animated bar would be displayed in interactive console sessions. ([#1649](https://github.com/beeware/briefcase/issues/1649))
- Additional options can now be passed to the `docker build` command for building native Linux packages and AppImages via the `--Xdocker-build` argument. ([#1661](https://github.com/beeware/briefcase/issues/1661))
- The contents of `pyproject.toml` is now included in the log file. ([#1674](https://github.com/beeware/briefcase/issues/1674))
- When an app runs on an Android device or emulator, the logging output is now colored. ([#1676](https://github.com/beeware/briefcase/issues/1676))
- When deep debug is activated via `-vv`, `pip` now installs requirements for the app with verbose logging. ([#1708](https://github.com/beeware/briefcase/issues/1708))
- The listing of filenames for updating permissions for building native Linux packages is now only shown when verbose logging is enabled via `-v`. ([#1720](https://github.com/beeware/briefcase/issues/1720))
- When a platform supports a splash screen, that splash screen will be generated automatically based on the app icon, rather than requiring additional configuration. ([#1737](https://github.com/beeware/briefcase/issues/1737))
- New projects for Toga on GTK3 now recommend using `gir1.2-webkit2-4.1` instead of `gir1.2-webkit2-4.0` for `WebView` support. ([#1748](https://github.com/beeware/briefcase/issues/1748))

### Bugfixes

- When Briefcase can't find `rpmbuild` on an RPM-based system, the message giving install instructions now uses the correct package name. ([#1638](https://github.com/beeware/briefcase/issues/1638))
- Creating new projects is now compatible with cookiecutter v2.6.0. ([#1663](https://github.com/beeware/briefcase/issues/1663))
- The minimum version of pip was bumped to 23.1.2 to ensure compatibility with Python 3.12. ([#1681](https://github.com/beeware/briefcase/issues/1681))
- On Windows, the Android emulator will always open without needing to press CTRL-C. ([#1687](https://github.com/beeware/briefcase/issues/1687))
- A spurious Android emulator named `@INFO` will no longer be included in the list of available emulators. ([#1697](https://github.com/beeware/briefcase/issues/1697))
- The configuration generated for iOS apps declaring geolocation permissions has been corrected. ([#1713](https://github.com/beeware/briefcase/issues/1713))
- When using `-r/--update-requirements` for building for Android, the app's requirements are always reinstalled now. ([#1721](https://github.com/beeware/briefcase/issues/1721))
- When creating a new project, the validation for App Name now rejects all non-ASCII values. ([#1762](https://github.com/beeware/briefcase/issues/1762))
- Packages created for OpenSUSE now depend on `libcanberra-gtk3-module` instead of `libcanberra-gtk3-0`. ([#1774](https://github.com/beeware/briefcase/issues/1774))

### Backward Incompatible Changes

- WiX v3.14.1 is now used to package Windows apps. Run `briefcase upgrade wix` to start using this version. ([#1707](https://github.com/beeware/briefcase/issues/1707))
- Java JDK 17.0.11+9 is now used to package Android apps. Use `briefcase upgrade java` to update your Briefcase-installed JDK instance to this version. ([#1736](https://github.com/beeware/briefcase/issues/1736))
- The `splash` configuration option will no longer be honored. Splash screens are now generated based on the icon image. ([#1737](https://github.com/beeware/briefcase/issues/1737))
- iOS apps now require 640px, 1280px and 1920px icon image. ([#1737](https://github.com/beeware/briefcase/issues/1737))
- Android apps now require an `adaptive` variant for icons. This requires 108px, 162px, 216px, 324px and 432px images with a transparent background. The Android `square` icon variant requires additional 320px, 480px, 640px, 960px and 1280px images. ([#1737](https://github.com/beeware/briefcase/issues/1737))

### Documentation

- The documentation contribution guide was updated to use a more authoritative reStructuredText reference. ([#1695](https://github.com/beeware/briefcase/issues/1695))
- The README badges were updated to display correctly on GitHub. ([#1763](https://github.com/beeware/briefcase/issues/1763))

### Misc

- [#1428](https://github.com/beeware/briefcase/issues/1428), [#1495](https://github.com/beeware/briefcase/issues/1495), [#1637](https://github.com/beeware/briefcase/issues/1637), [#1639](https://github.com/beeware/briefcase/issues/1639), [#1642](https://github.com/beeware/briefcase/issues/1642), [#1643](https://github.com/beeware/briefcase/issues/1643), [#1644](https://github.com/beeware/briefcase/issues/1644), [#1645](https://github.com/beeware/briefcase/issues/1645), [#1646](https://github.com/beeware/briefcase/issues/1646), [#1652](https://github.com/beeware/briefcase/issues/1652), [#1653](https://github.com/beeware/briefcase/issues/1653), [#1656](https://github.com/beeware/briefcase/issues/1656), [#1657](https://github.com/beeware/briefcase/issues/1657), [#1658](https://github.com/beeware/briefcase/issues/1658), [#1659](https://github.com/beeware/briefcase/issues/1659), [#1660](https://github.com/beeware/briefcase/issues/1660), [#1666](https://github.com/beeware/briefcase/issues/1666), [#1671](https://github.com/beeware/briefcase/issues/1671), [#1672](https://github.com/beeware/briefcase/issues/1672), [#1679](https://github.com/beeware/briefcase/issues/1679), [#1683](https://github.com/beeware/briefcase/issues/1683), [#1684](https://github.com/beeware/briefcase/issues/1684), [#1686](https://github.com/beeware/briefcase/issues/1686), [#1689](https://github.com/beeware/briefcase/issues/1689), [#1690](https://github.com/beeware/briefcase/issues/1690), [#1691](https://github.com/beeware/briefcase/issues/1691), [#1692](https://github.com/beeware/briefcase/issues/1692), [#1694](https://github.com/beeware/briefcase/issues/1694), [#1699](https://github.com/beeware/briefcase/issues/1699), [#1700](https://github.com/beeware/briefcase/issues/1700), [#1701](https://github.com/beeware/briefcase/issues/1701), [#1702](https://github.com/beeware/briefcase/issues/1702), [#1710](https://github.com/beeware/briefcase/issues/1710), [#1711](https://github.com/beeware/briefcase/issues/1711), [#1712](https://github.com/beeware/briefcase/issues/1712), [#1716](https://github.com/beeware/briefcase/issues/1716), [#1717](https://github.com/beeware/briefcase/issues/1717), [#1722](https://github.com/beeware/briefcase/issues/1722), [#1723](https://github.com/beeware/briefcase/issues/1723), [#1725](https://github.com/beeware/briefcase/issues/1725), [#1730](https://github.com/beeware/briefcase/issues/1730), [#1731](https://github.com/beeware/briefcase/issues/1731), [#1732](https://github.com/beeware/briefcase/issues/1732), [#1741](https://github.com/beeware/briefcase/issues/1741), [#1742](https://github.com/beeware/briefcase/issues/1742), [#1743](https://github.com/beeware/briefcase/issues/1743), [#1744](https://github.com/beeware/briefcase/issues/1744), [#1745](https://github.com/beeware/briefcase/issues/1745), [#1752](https://github.com/beeware/briefcase/issues/1752), [#1753](https://github.com/beeware/briefcase/issues/1753), [#1754](https://github.com/beeware/briefcase/issues/1754), [#1756](https://github.com/beeware/briefcase/issues/1756), [#1757](https://github.com/beeware/briefcase/issues/1757), [#1758](https://github.com/beeware/briefcase/issues/1758), [#1759](https://github.com/beeware/briefcase/issues/1759), [#1760](https://github.com/beeware/briefcase/issues/1760), [#1761](https://github.com/beeware/briefcase/issues/1761), [#1766](https://github.com/beeware/briefcase/issues/1766), [#1769](https://github.com/beeware/briefcase/issues/1769), [#1775](https://github.com/beeware/briefcase/issues/1775), [#1776](https://github.com/beeware/briefcase/issues/1776)

## 0.3.17 (2024-02-06)

### Features

- Android apps are now able to customize the libraries included in the app at build time. ([#485](https://github.com/beeware/briefcase/issues/485))
- App permissions can now be declared as part of an app's configuration. ([#547](https://github.com/beeware/briefcase/issues/547))
- The `-C`/`--config` option can now be used to override app settings from the command line. ([#1115](https://github.com/beeware/briefcase/issues/1115))
- The verbosity flag, `-v`, was expanded to support three levels of logging verbosity. ([#1501](https://github.com/beeware/briefcase/issues/1501))
- Briefcase now supports GUI bootstrap plugins to customize how new projects are created. ([#1524](https://github.com/beeware/briefcase/issues/1524))
- GitPython's debug logging is now included in deep debug output. ([#1529](https://github.com/beeware/briefcase/issues/1529))
- RCEdit v2.0.0 is now used to build Windows apps. Run `briefcase upgrade` to use this latest version. ([#1543](https://github.com/beeware/briefcase/issues/1543))
- The Flatpak runtimes for new projects were updated. `org.freedesktop.Platform` will now default to 23.08; `org.gnome.Platform` will now default to 45; and `org.kde.Platform` will now default to 6.6. ([#1545](https://github.com/beeware/briefcase/issues/1545))
- When creating new projects with the `briefcase new` command, project configuration overrides can be specified via the `-Q` command line argument. For instance, a specific license can be specified with `-Q "license=MIT license"`. ([#1552](https://github.com/beeware/briefcase/issues/1552))
- New virtual devices for the Android emulator are created using the Pixel 7 Pro skin. ([#1554](https://github.com/beeware/briefcase/issues/1554))
- The web server for running static web projects now falls back to a system allocated port if the requested port is already in use. ([#1561](https://github.com/beeware/briefcase/issues/1561))
- Flatpaks are now created with permissions to access the GPU and sound devices. ([#1563](https://github.com/beeware/briefcase/issues/1563))
- AppImages can now be built for the ARM architecture. ([#1564](https://github.com/beeware/briefcase/issues/1564))
- Apps can now specify a primary color (for both light and dark modes), and an accent color. If the platform allows apps to customize color use, these colors will be used to style the app's presentation. ([#1566](https://github.com/beeware/briefcase/issues/1566))
- The version of PursuedPyBear for new projects was bumped from 1.1 to 3.2.0. ([#1592](https://github.com/beeware/briefcase/issues/1592))
- Python 3.12 is now supported on Android. ([#1596](https://github.com/beeware/briefcase/issues/1596))
- Android apps can now specify the base theme used to style the application. ([#1610](https://github.com/beeware/briefcase/issues/1610))
- The Java JDK was upgraded from 17.0.8.1+1 to 17.0.10+7. Run `briefcase upgrade java` to upgrade existing Briefcase installations. ([#1611](https://github.com/beeware/briefcase/issues/1611))
- When the Android emulator fails to start up properly, users are now presented with additional resources to help resolve any issues. ([#1630](https://github.com/beeware/briefcase/issues/1630))

### Bugfixes

- When a custom Briefcase template from a git repository is used to create an app, Briefcase now ensures that git repository is always used. ([#1158](https://github.com/beeware/briefcase/issues/1158))
- The filter for iOS build warnings was improved to catch messages from Xcode 15.0.1. ([#1507](https://github.com/beeware/briefcase/issues/1507))
- When merging dependencies on macOS, file permissions are now preserved. ([#1510](https://github.com/beeware/briefcase/issues/1510))
- `flatpak-builder` 1.3+ can now be correctly identified. ([#1513](https://github.com/beeware/briefcase/issues/1513))
- The BeeWare icon of Brutus is now used as the runtime icon for new projects created with PyGame. ([#1532](https://github.com/beeware/briefcase/issues/1532))
- Linux System RPM packaging for openSUSE Tumbleweed no longer errors with `FileNotFoundError`. ([#1595](https://github.com/beeware/briefcase/issues/1595))
- Any ANSI escape sequences or console control codes are now stripped in all output captured in the Briefcase log file. ([#1604](https://github.com/beeware/briefcase/issues/1604))
- The detection of physical Android devices on macOS was made more resilient. ([#1627](https://github.com/beeware/briefcase/issues/1627))

### Backward Incompatible Changes

- The use of AppImage as an output format now generates a warning. ([#1500](https://github.com/beeware/briefcase/issues/1500))
- Support for creating new projects using PySide2 has been removed. Briefcase's release testing will no longer explicitly verify compatibility with PySide2. ([#1524](https://github.com/beeware/briefcase/issues/1524))
- The Flatpak build process no longer strips binaries included in third-party (e.g. PyPI) packages that are bundled with the app. ([#1540](https://github.com/beeware/briefcase/issues/1540))
- New projects will now use `manylinux_2_28` instead of `manylinux2014` to create AppImages in Docker. ([#1564](https://github.com/beeware/briefcase/issues/1564))
- It is highly recommended that Android applications add a definition for `build_gradle_dependencies` to their app configuration. A default value will be used if this option is not explicitly provided. Refer to [the Android documentation](https://briefcase.beeware.org/en/latest/reference/platforms/android/gradle#android.build_gradle_dependencies) for the default value that will be used. ([#1610](https://github.com/beeware/briefcase/issues/1610))

### Documentation

- The common options available to every command have now been documented. ([#1517](https://github.com/beeware/briefcase/issues/1517))

### Misc

- [#1504](https://github.com/beeware/briefcase/issues/1504), [#1505](https://github.com/beeware/briefcase/issues/1505), [#1506](https://github.com/beeware/briefcase/issues/1506), [#1515](https://github.com/beeware/briefcase/issues/1515), [#1516](https://github.com/beeware/briefcase/issues/1516), [#1518](https://github.com/beeware/briefcase/issues/1518), [#1519](https://github.com/beeware/briefcase/issues/1519), [#1526](https://github.com/beeware/briefcase/issues/1526), [#1527](https://github.com/beeware/briefcase/issues/1527), [#1533](https://github.com/beeware/briefcase/issues/1533), [#1534](https://github.com/beeware/briefcase/issues/1534), [#1535](https://github.com/beeware/briefcase/issues/1535), [#1536](https://github.com/beeware/briefcase/issues/1536), [#1538](https://github.com/beeware/briefcase/issues/1538), [#1541](https://github.com/beeware/briefcase/issues/1541), [#1548](https://github.com/beeware/briefcase/issues/1548), [#1549](https://github.com/beeware/briefcase/issues/1549), [#1550](https://github.com/beeware/briefcase/issues/1550), [#1551](https://github.com/beeware/briefcase/issues/1551), [#1555](https://github.com/beeware/briefcase/issues/1555), [#1556](https://github.com/beeware/briefcase/issues/1556), [#1557](https://github.com/beeware/briefcase/issues/1557), [#1560](https://github.com/beeware/briefcase/issues/1560), [#1562](https://github.com/beeware/briefcase/issues/1562), [#1567](https://github.com/beeware/briefcase/issues/1567), [#1568](https://github.com/beeware/briefcase/issues/1568), [#1569](https://github.com/beeware/briefcase/issues/1569), [#1571](https://github.com/beeware/briefcase/issues/1571), [#1575](https://github.com/beeware/briefcase/issues/1575), [#1576](https://github.com/beeware/briefcase/issues/1576), [#1579](https://github.com/beeware/briefcase/issues/1579), [#1582](https://github.com/beeware/briefcase/issues/1582), [#1585](https://github.com/beeware/briefcase/issues/1585), [#1586](https://github.com/beeware/briefcase/issues/1586), [#1589](https://github.com/beeware/briefcase/issues/1589), [#1590](https://github.com/beeware/briefcase/issues/1590), [#1597](https://github.com/beeware/briefcase/issues/1597), [#1606](https://github.com/beeware/briefcase/issues/1606), [#1607](https://github.com/beeware/briefcase/issues/1607), [#1613](https://github.com/beeware/briefcase/issues/1613), [#1614](https://github.com/beeware/briefcase/issues/1614), [#1615](https://github.com/beeware/briefcase/issues/1615), [#1618](https://github.com/beeware/briefcase/issues/1618), [#1621](https://github.com/beeware/briefcase/issues/1621), [#1622](https://github.com/beeware/briefcase/issues/1622), [#1623](https://github.com/beeware/briefcase/issues/1623), [#1624](https://github.com/beeware/briefcase/issues/1624), [#1628](https://github.com/beeware/briefcase/issues/1628), [#1632](https://github.com/beeware/briefcase/issues/1632), [#1633](https://github.com/beeware/briefcase/issues/1633)

## 0.3.16 (2023-10-20)

### Features

- Support for less common environments, such as Linux on ARM, has been improved. Error messages for unsupported platforms are now more accurate. ([#1360](https://github.com/beeware/briefcase/pull/1360))
- Tool verification for Java, Android SDK, and WiX have been improved to provide more informative errors and debug logging. ([#1382](https://github.com/beeware/briefcase/pull/1382))
- A super verbose logging mode was added (enabled using `-vv`). This turns on all Briefcase internal logging, but also enables verbose logging for all the third-party tools that Briefcase invokes. ([#1384](https://github.com/beeware/briefcase/issues/1384))
- Briefcase now uses Android SDK Command-Line Tools v9.0. If an externally-managed Android SDK is being used, it must provide this version of Command-Line Tools. Use the SDK Manager in Android Studio to ensure it is installed. ([#1397](https://github.com/beeware/briefcase/pull/1397))
- Support for OpenSuSE Linux distributions was added. ([#1416](https://github.com/beeware/briefcase/issues/1416))
- iOS apps are no longer rejected by the iOS App Store for packaging reasons. ([#1439](https://github.com/beeware/briefcase/pull/1439))
- The Java JDK version was upgraded to 17.0.8.1+1. ([#1462](https://github.com/beeware/briefcase/pull/1462))
- macOS apps can now be configured to produce single platform binaries, or binaries that will work on both x86_64 and ARM64. ([#1482](https://github.com/beeware/briefcase/issues/1482))

### Bugfixes

- Build warnings caused by bugs in Xcode that can be safely ignored are now filtered out of visible output. ([#377](https://github.com/beeware/briefcase/issues/377))
- The run command now ensures Android logging is shown when the datetime on the device is different from the host machine. ([#1146](https://github.com/beeware/briefcase/issues/1146))
- Briefcase will detect if you attempt to launch an Android app on a device whose OS doesn't meet minimum version requirements. ([#1157](https://github.com/beeware/briefcase/issues/1157))
- macOS apps are now guaranteed to be universal binaries, even when dependencies only provide single-architecture binary wheels. ([#1217](https://github.com/beeware/briefcase/issues/1217))
- The ability to build AppImages in Docker on macOS was restored. ([#1352](https://github.com/beeware/briefcase/issues/1352))
- Error reporting has been improved when the target Docker image name is invalid. ([#1368](https://github.com/beeware/briefcase/issues/1368))
- Creating Debian packages no longer fails due to a permission error for certain `umask` values (such as `0077`). ([#1369](https://github.com/beeware/briefcase/issues/1369))
- Inside of Docker containers, the Briefcase data directory is now mounted at `/briefcase` instead of `/home/brutus/.cache/briefcase`. ([#1374](https://github.com/beeware/briefcase/issues/1374))
- The console output from invoking Python via a subprocess call is now properly decoded as UTF-8. ([#1407](https://github.com/beeware/briefcase/issues/1407))
- The command line arguments used to configure the Python environment for `briefcase dev` no longer leak into the runtime environment on macOS. ([#1413](https://github.com/beeware/briefcase/pull/1413))

### Backward Incompatible Changes

- AppImage packaging requires a recent release of LinuxDeploy to continue creating AppImages. Run `briefcase upgrade linuxdeploy` to install the latest version. ([#1361](https://github.com/beeware/briefcase/issues/1361))
- The size of iOS splash images have changed. iOS apps should now provide 800px, 1600px and 2400px images (previously, this as 1024px, 2048px and 3072px). This is because iOS 14 added a hard limit on the size of image resources. ([#1371](https://github.com/beeware/briefcase/pull/1371))
- Support for AppImage has been reduced to "best effort". We will maintain unit test coverage for the AppImage backend, but we no longer build AppImages as part of our release process. We will accept bug reports related to AppImage support, and we will merge PRs that address AppImage support, but the core team no longer considers addressing AppImage bugs a priority, and discourages the use of AppImage for new projects. ([#1449](https://github.com/beeware/briefcase/pull/1449))

### Documentation

- Documentation on the process of retrieving certificate identities on macOS and Windows was improved. ([#1473](https://github.com/beeware/briefcase/pull/1473))

### Misc

- [#1136](https://github.com/beeware/briefcase/issues/1136), [#1290](https://github.com/beeware/briefcase/pull/1290), [#1363](https://github.com/beeware/briefcase/pull/1363), [#1364](https://github.com/beeware/briefcase/pull/1364), [#1365](https://github.com/beeware/briefcase/pull/1365), [#1372](https://github.com/beeware/briefcase/pull/1372), [#1375](https://github.com/beeware/briefcase/pull/1375), [#1376](https://github.com/beeware/briefcase/pull/1376), [#1379](https://github.com/beeware/briefcase/issues/1379), [#1388](https://github.com/beeware/briefcase/pull/1388), [#1394](https://github.com/beeware/briefcase/pull/1394), [#1395](https://github.com/beeware/briefcase/pull/1395), [#1396](https://github.com/beeware/briefcase/pull/1396), [#1398](https://github.com/beeware/briefcase/pull/1398), [#1400](https://github.com/beeware/briefcase/pull/1400), [#1401](https://github.com/beeware/briefcase/pull/1401), [#1402](https://github.com/beeware/briefcase/pull/1402), [#1403](https://github.com/beeware/briefcase/pull/1403), [#1408](https://github.com/beeware/briefcase/pull/1408), [#1409](https://github.com/beeware/briefcase/pull/1409), [#1410](https://github.com/beeware/briefcase/pull/1410), [#1411](https://github.com/beeware/briefcase/issues/1411), [#1412](https://github.com/beeware/briefcase/pull/1412), [#1418](https://github.com/beeware/briefcase/pull/1418), [#1419](https://github.com/beeware/briefcase/pull/1419), [#1420](https://github.com/beeware/briefcase/pull/1420), [#1421](https://github.com/beeware/briefcase/pull/1421), [#1427](https://github.com/beeware/briefcase/pull/1427), [#1429](https://github.com/beeware/briefcase/issues/1429), [#1431](https://github.com/beeware/briefcase/issues/1431), [#1433](https://github.com/beeware/briefcase/pull/1433), [#1435](https://github.com/beeware/briefcase/pull/1435), [#1436](https://github.com/beeware/briefcase/pull/1436), [#1437](https://github.com/beeware/briefcase/pull/1437), [#1438](https://github.com/beeware/briefcase/pull/1438), [#1442](https://github.com/beeware/briefcase/pull/1442), [#1443](https://github.com/beeware/briefcase/pull/1443), [#1444](https://github.com/beeware/briefcase/pull/1444), [#1445](https://github.com/beeware/briefcase/pull/1445), [#1446](https://github.com/beeware/briefcase/pull/1446), [#1447](https://github.com/beeware/briefcase/pull/1447), [#1448](https://github.com/beeware/briefcase/pull/1448), [#1454](https://github.com/beeware/briefcase/pull/1454), [#1455](https://github.com/beeware/briefcase/pull/1455), [#1456](https://github.com/beeware/briefcase/pull/1456), [#1457](https://github.com/beeware/briefcase/pull/1457), [#1464](https://github.com/beeware/briefcase/pull/1464), [#1465](https://github.com/beeware/briefcase/pull/1465), [#1466](https://github.com/beeware/briefcase/pull/1466), [#1470](https://github.com/beeware/briefcase/pull/1470), [#1474](https://github.com/beeware/briefcase/pull/1474), [#1476](https://github.com/beeware/briefcase/pull/1476), [#1477](https://github.com/beeware/briefcase/pull/1477), [#1478](https://github.com/beeware/briefcase/pull/1478), [#1481](https://github.com/beeware/briefcase/issues/1481), [#1485](https://github.com/beeware/briefcase/pull/1485), [#1486](https://github.com/beeware/briefcase/pull/1486), [#1487](https://github.com/beeware/briefcase/pull/1487), [#1488](https://github.com/beeware/briefcase/pull/1488), [#1489](https://github.com/beeware/briefcase/pull/1489), [#1490](https://github.com/beeware/briefcase/pull/1490), [#1492](https://github.com/beeware/briefcase/pull/1492), [#1494](https://github.com/beeware/briefcase/pull/1494)

## 0.3.15 (2023-07-10)

### Features

- Windows apps can now be packaged as simple ZIP files. ([#457](https://github.com/beeware/briefcase/issues/457))
- An Android SDK specified in `ANDROID_HOME` is respected now and will take precedence over the setting of `ANDROID_SDK_ROOT`. ([#463](https://github.com/beeware/briefcase/issues/463))
- Android support was upgraded to use Java 17 for builds. ([#1065](https://github.com/beeware/briefcase/issues/1065))
- On Linux, Docker Desktop and rootless Docker are now supported. ([#1083](https://github.com/beeware/briefcase/issues/1083))
- The company/author name in the installation path for Windows MSI installers is now optional. ([#1199](https://github.com/beeware/briefcase/issues/1199))
- macOS code signing is now multi-threaded (and therefore much faster!) ([#1201](https://github.com/beeware/briefcase/issues/1201))
- Briefcase will now honor PEP-621 project fields where they map to Briefcase configuration items. ([#1203](https://github.com/beeware/briefcase/issues/1203))

### Bugfixes

- XML compatibility warnings generated by the Android build have been cleaned up. ([#827](https://github.com/beeware/briefcase/issues/827))
- Non ASCII characters provided in the `briefcase new` wizard are quoted before being put into `pyproject.toml`. ([#1011](https://github.com/beeware/briefcase/issues/1011))
- Requests to the web server are now recorded in the log file. ([#1090](https://github.com/beeware/briefcase/issues/1090))
- An "Invalid Keystore format" error is no longer raised when signing an app if the local Android keystore was generated with a recent version of Java. ([#1112](https://github.com/beeware/briefcase/issues/1112))
- Content before a closing square bracket (`]`) or `.so)` is no longer stripped by the macOS and iOS log filter. ([#1179](https://github.com/beeware/briefcase/issues/1179))
- The option to run Linux system packages through Docker was removed. ([#1207](https://github.com/beeware/briefcase/issues/1207))
- Error handling for incomplete or corrupted GitHub clones of templates has been improved. ([#1210](https://github.com/beeware/briefcase/pull/1210))
- Application/Bundle IDs are normalized to replace underscores with dashes when possible ([#1234](https://github.com/beeware/briefcase/pull/1234))
- Filenames and directories in RPM package definitions are quoted in order to include filenames that include white space. ([#1236](https://github.com/beeware/briefcase/issues/1236))
- Briefcase will no longer display progress bars if the `FORCE_COLOR` environment variable is set. ([#1267](https://github.com/beeware/briefcase/pull/1267))
- When creating a new Briefcase project, the header line in `pyproject.toml` now contains the version of Briefcase instead of "Unknown". ([#1276](https://github.com/beeware/briefcase/pull/1276))
- Android logs no longer include timestamp and PID, making them easier to read on narrow screens. ([#1286](https://github.com/beeware/briefcase/pull/1286))
- An warning is no longer logged if the Java identified by macOS is not usable by Briefcase. ([#1305](https://github.com/beeware/briefcase/issues/1305))
- Incompatibilities with Cookiecutter 2.2.0 have been resolved. ([#1347](https://github.com/beeware/briefcase/issues/1347))

### Backward Incompatible Changes

- Names matching modules in the Python standard library, and `main`, can no longer be used as an application name. ([#853](https://github.com/beeware/briefcase/issues/853))
- The `--no-sign` option for packaging was removed. Briefcase will now prompt for a signing identity during packaging, falling back to adhoc/no signing as a default where possible. ([#865](https://github.com/beeware/briefcase/issues/865))
- The version of OpenJDK for Java was updated from 8 to 17. Any Android apps generated on previous versions of Briefcase must be re-generated by running `briefcase create android gradle`. If customizations were made to files within the generated app, they will need to be manually re-applied after re-running the create command. ([#1065](https://github.com/beeware/briefcase/issues/1065))
- Flatpak apps no longer default to using the Freedesktop runtime and SDK version 21.08 when a runtime is not specified. Instead, the runtime now must be explicitly defined in the [application configuration](https://briefcase.beeware.org/en/latest/reference/platforms/linux/flatpak#application-configuration). ([#1272](https://github.com/beeware/briefcase/pull/1272))

### Documentation

- All code blocks were updated to add a button to copy the relevant contents on to the user's clipboard. ([#1213](https://github.com/beeware/briefcase/pull/1213))
- The limitations of using WebKit2 in AppImage were documented. ([#1322](https://github.com/beeware/briefcase/issues/1322))

### Misc

- [#856](https://github.com/beeware/briefcase/issues/856), [#1093](https://github.com/beeware/briefcase/pull/1093), [#1178](https://github.com/beeware/briefcase/pull/1178), [#1181](https://github.com/beeware/briefcase/pull/1181), [#1186](https://github.com/beeware/briefcase/pull/1186), [#1187](https://github.com/beeware/briefcase/issues/1187), [#1191](https://github.com/beeware/briefcase/pull/1191), [#1192](https://github.com/beeware/briefcase/pull/1192), [#1193](https://github.com/beeware/briefcase/pull/1193), [#1195](https://github.com/beeware/briefcase/issues/1195), [#1197](https://github.com/beeware/briefcase/pull/1197), [#1200](https://github.com/beeware/briefcase/pull/1200), [#1204](https://github.com/beeware/briefcase/pull/1204), [#1205](https://github.com/beeware/briefcase/pull/1205), [#1206](https://github.com/beeware/briefcase/pull/1206), [#1215](https://github.com/beeware/briefcase/pull/1215), [#1226](https://github.com/beeware/briefcase/pull/1226), [#1228](https://github.com/beeware/briefcase/pull/1228), [#1232](https://github.com/beeware/briefcase/pull/1232), [#1233](https://github.com/beeware/briefcase/pull/1233), [#1239](https://github.com/beeware/briefcase/pull/1239), [#1241](https://github.com/beeware/briefcase/pull/1241), [#1242](https://github.com/beeware/briefcase/pull/1242), [#1243](https://github.com/beeware/briefcase/pull/1243), [#1244](https://github.com/beeware/briefcase/pull/1244), [#1246](https://github.com/beeware/briefcase/pull/1246), [#1248](https://github.com/beeware/briefcase/pull/1248), [#1249](https://github.com/beeware/briefcase/issues/1249), [#1253](https://github.com/beeware/briefcase/pull/1253), [#1254](https://github.com/beeware/briefcase/pull/1254), [#1255](https://github.com/beeware/briefcase/pull/1255), [#1257](https://github.com/beeware/briefcase/pull/1257), [#1258](https://github.com/beeware/briefcase/pull/1258), [#1262](https://github.com/beeware/briefcase/pull/1262), [#1263](https://github.com/beeware/briefcase/pull/1263), [#1264](https://github.com/beeware/briefcase/pull/1264), [#1265](https://github.com/beeware/briefcase/pull/1265), [#1273](https://github.com/beeware/briefcase/pull/1273), [#1274](https://github.com/beeware/briefcase/pull/1274), [#1279](https://github.com/beeware/briefcase/pull/1279), [#1282](https://github.com/beeware/briefcase/pull/1282), [#1283](https://github.com/beeware/briefcase/pull/1283), [#1284](https://github.com/beeware/briefcase/pull/1284), [#1293](https://github.com/beeware/briefcase/pull/1293), [#1294](https://github.com/beeware/briefcase/pull/1294), [#1295](https://github.com/beeware/briefcase/pull/1295), [#1299](https://github.com/beeware/briefcase/pull/1299), [#1300](https://github.com/beeware/briefcase/pull/1300), [#1301](https://github.com/beeware/briefcase/pull/1301), [#1310](https://github.com/beeware/briefcase/pull/1310), [#1311](https://github.com/beeware/briefcase/pull/1311), [#1316](https://github.com/beeware/briefcase/pull/1316), [#1317](https://github.com/beeware/briefcase/pull/1317), [#1323](https://github.com/beeware/briefcase/pull/1323), [#1324](https://github.com/beeware/briefcase/pull/1324), [#1333](https://github.com/beeware/briefcase/pull/1333), [#1334](https://github.com/beeware/briefcase/pull/1334), [#1335](https://github.com/beeware/briefcase/pull/1335), [#1336](https://github.com/beeware/briefcase/pull/1336), [#1339](https://github.com/beeware/briefcase/issues/1339), [#1341](https://github.com/beeware/briefcase/pull/1341), [#1350](https://github.com/beeware/briefcase/pull/1350), [#1351](https://github.com/beeware/briefcase/pull/1351)

## 0.3.14 (2023-04-12)

### Features

- Added support for code signing Windows apps. ([#366](https://github.com/beeware/briefcase/issues/366))
- The base image used to build AppImages is now user-configurable. ([#947](https://github.com/beeware/briefcase/issues/947))
- Support for Arch `.pkg.tar.zst` packaging was added to the Linux system backend. ([#1064](https://github.com/beeware/briefcase/issues/1064))
- Pygame was added as an explicit option for a GUI toolkit. ([#1125](https://github.com/beeware/briefcase/pull/1125))
- AppImage and Flatpak builds now use [indygreg's Python Standalone Builds](https://github.com/astral-sh/python-build-standalone) to provide Python support. ([#1132](https://github.com/beeware/briefcase/pull/1132))
- BeeWare now has a presence on Mastodon. ([#1142](https://github.com/beeware/briefcase/pull/1142))

### Bugfixes

- When commands produce output that cannot be decoded to Unicode, Briefcase now writes the bytes as hex instead of truncating output or canceling the command altogether. ([#1141](https://github.com/beeware/briefcase/issues/1141))
- When `JAVA_HOME` contains a path to a file instead of a directory, Briefcase will now warn the user and install an isolated copy of Java instead of logging a `NotADirectoryError`. ([#1144](https://github.com/beeware/briefcase/pull/1144))
- If the Docker `buildx` plugin is not installed, users are now directed by Briefcase to install it instead of Docker failing to build the image. ([#1153](https://github.com/beeware/briefcase/pull/1153))

### Misc

- [#1133](https://github.com/beeware/briefcase/pull/1133), [#1138](https://github.com/beeware/briefcase/pull/1138), [#1139](https://github.com/beeware/briefcase/pull/1139), [#1140](https://github.com/beeware/briefcase/pull/1140), [#1147](https://github.com/beeware/briefcase/pull/1147), [#1148](https://github.com/beeware/briefcase/pull/1148), [#1149](https://github.com/beeware/briefcase/pull/1149), [#1150](https://github.com/beeware/briefcase/pull/1150), [#1151](https://github.com/beeware/briefcase/pull/1151), [#1156](https://github.com/beeware/briefcase/pull/1156), [#1162](https://github.com/beeware/briefcase/pull/1162), [#1163](https://github.com/beeware/briefcase/pull/1163), [#1168](https://github.com/beeware/briefcase/pull/1168), [#1169](https://github.com/beeware/briefcase/pull/1169), [#1170](https://github.com/beeware/briefcase/pull/1170), [#1171](https://github.com/beeware/briefcase/pull/1171), [#1172](https://github.com/beeware/briefcase/pull/1172), [#1173](https://github.com/beeware/briefcase/pull/1173), [#1177](https://github.com/beeware/briefcase/pull/1177)

## 0.3.13 (2023-03-10)

### Features

- Distribution artefacts are now generated into a single `dist` folder. ([#424](https://github.com/beeware/briefcase/issues/424))
- When installing application sources and dependencies, any `__pycache__` folders are now automatically removed. ([#986](https://github.com/beeware/briefcase/issues/986))
- A Linux System backend was added, supporting `.deb` as a packaging format. ([#1062](https://github.com/beeware/briefcase/issues/1062))
- Support for `.rpm` packaging was added to the Linux system backend. ([#1063](https://github.com/beeware/briefcase/issues/1063))
- Support for passthrough arguments was added to the `dev` and `run` commands. ([#1077](https://github.com/beeware/briefcase/issues/1077))
- Users can now define custom content to include in their `pyscript.toml` configuration file for web deployments. ([#1089](https://github.com/beeware/briefcase/issues/1089))
- The `new` command now allows for specifying a custom template branch, as well as a custom template. ([#1101](https://github.com/beeware/briefcase/pull/1101))

### Bugfixes

- Spaces are no longer used in the paths for generated app templates. ([#804](https://github.com/beeware/briefcase/issues/804))
- The stub executable used by Windows now clears the threading mode before starting the Python app. This caused problems with displaying dialogs in Qt apps. ([#930](https://github.com/beeware/briefcase/issues/930))
- Briefcase now prevents running commands targeting Windows platforms when not on Windows. ([#1010](https://github.com/beeware/briefcase/issues/1010))
- The command to store notarization credentials no longer causes Briefcase to hang. ([#1100](https://github.com/beeware/briefcase/pull/1100))
- macOS developer tool installation prompts have been improved. ([#1122](https://github.com/beeware/briefcase/pull/1122))

### Misc

- [#1070](https://github.com/beeware/briefcase/pull/1070), [#1074](https://github.com/beeware/briefcase/pull/1074), [#1075](https://github.com/beeware/briefcase/pull/1075), [#1076](https://github.com/beeware/briefcase/pull/1076), [#1080](https://github.com/beeware/briefcase/pull/1080), [#1084](https://github.com/beeware/briefcase/pull/1084), [#1085](https://github.com/beeware/briefcase/pull/1085), [#1086](https://github.com/beeware/briefcase/pull/1086), [#1087](https://github.com/beeware/briefcase/issues/1087), [#1094](https://github.com/beeware/briefcase/pull/1094), [#1096](https://github.com/beeware/briefcase/pull/1096), [#1097](https://github.com/beeware/briefcase/pull/1097), [#1098](https://github.com/beeware/briefcase/pull/1098), [#1103](https://github.com/beeware/briefcase/pull/1103), [#1109](https://github.com/beeware/briefcase/pull/1109), [#1110](https://github.com/beeware/briefcase/pull/1110), [#1111](https://github.com/beeware/briefcase/pull/1111), [#1119](https://github.com/beeware/briefcase/pull/1119), [#1120](https://github.com/beeware/briefcase/pull/1120), [#1130](https://github.com/beeware/briefcase/pull/1130)

## 0.3.12 (2023-01-30)

### Features

- Briefcase is more resilient to file download failures by discarding partially downloaded files. ([#753](https://github.com/beeware/briefcase/issues/753))
- All warnings from the App and its dependencies are now shown when running `briefcase dev` by invoking Python in [development mode](https://docs.python.org/3/library/devmode.html). ([#806](https://github.com/beeware/briefcase/issues/806))
- The Dockerfile used to build AppImages can now include user-provided container setup instructions. ([#886](https://github.com/beeware/briefcase/issues/886))
- It is no longer necessary to specify a device when building an iOS project. ([#953](https://github.com/beeware/briefcase/pull/953))
- Briefcase apps can now provide a test suite. `briefcase run` and `briefcase dev` both provide a `--test` option to start the test suite. ([#962](https://github.com/beeware/briefcase/pull/962))
- Initial support for Python 3.12 was added. ([#965](https://github.com/beeware/briefcase/pull/965))
- Frameworks contained added to a macOS app bundle are now automatically code signed. ([#971](https://github.com/beeware/briefcase/pull/971))
- The `build.gradle` file used to build Android apps can now include arbitrary additional settings. ([#973](https://github.com/beeware/briefcase/issues/973))
- The run and build commands now have full control over the update of app requirements resources. ([#983](https://github.com/beeware/briefcase/pull/983))
- Resources that require variants will now use the variant name as part of the filename by default. ([#989](https://github.com/beeware/briefcase/pull/989))
- `briefcase open linux appimage` now starts a shell session in the Docker context, rather than opening the project folder. ([#991](https://github.com/beeware/briefcase/issues/991))
- Web project configuration has been updated to reflect recent changes to PyScript. ([#1004](https://github.com/beeware/briefcase/issues/1004))

### Bugfixes

- Console output of Windows apps is now captured in the Briefcase log. ([#787](https://github.com/beeware/briefcase/issues/787))
- Android emulators configured with `_no_skin` will no longer generate a warning. ([#882](https://github.com/beeware/briefcase/issues/882))
- Briefcase now exits normally when CTRL-C is sent while tailing logs for the App when using `briefcase run`. ([#904](https://github.com/beeware/briefcase/issues/904))
- Backslashes and double quotes are now safe to be used for formal name and description ([#905](https://github.com/beeware/briefcase/issues/905))
- The console output for Windows batch scripts in now captured in the Briefcase log. ([#917](https://github.com/beeware/briefcase/issues/917))
- When using the Windows Store version of Python, Briefcase now ensures the cache directory is created in `%LOCALAPPDATA%` instead of the sandboxed location enforced for Windows Store apps. ([#922](https://github.com/beeware/briefcase/issues/922))
- An Android application that successfully starts, but fails quickly, no longer stalls the launch process. ([#936](https://github.com/beeware/briefcase/issues/936))
- The required Visual Studio Code components are now included in verification errors for Visual Studio Apps. ([#939](https://github.com/beeware/briefcase/issues/939))
- It is now possible to specify app configurations for macOS Xcode and Windows Visual Studio projects. Previously, these sections of configuration files would be ignored due to a case discrepancy. ([#952](https://github.com/beeware/briefcase/pull/952))
- Development mode now starts apps in PEP540 UTF-8 mode, for consistency with the stub apps. ([#985](https://github.com/beeware/briefcase/pull/985))
- Local file references in requirements no longer break AppImage builds. ([#992](https://github.com/beeware/briefcase/issues/992))
- On macOS, Rosetta is now installed automatically if needed. ([#1000](https://github.com/beeware/briefcase/issues/1000))
- The way dependency versions are specified has been modified to make Briefcase as accommodating as possible with end-user environments, but as stable as possible for development environments. ([#1041](https://github.com/beeware/briefcase/pull/1041))
- To prevent console corruption, dynamic console elements (such as the Wait Bar) are temporarily removed when output streaming is disabled for a command. ([#1055](https://github.com/beeware/briefcase/issues/1055))

### Improved Documentation

- Release history now contains links to GitHub issues. ([#1022](https://github.com/beeware/briefcase/pull/1022))

### Misc

- \#906, \#907, \#918, \#923, \#924, \#925, \#926, \#929, \#931, \#951, \#959, \#960, \#964, \#967, \#969, \#972, \#981, \#984, \#987, \#994, \#995, \#996, \#997, \#1001, \#1002, \#1003, \#1012, \#1013, \#1020, \#1021, \#1023, \#1028, \#1038, \#1042, \#1043, \#1044, \#1045, \#1046, \#1047, \#1048, \#1049, \#1051, \#1052, \#1057, \#1059, \#1061, \#1068, \#1069, \#1071

## 0.3.11 (2022-10-14)

### Features

- Added support for deploying an app as a static web page using PyScript. (#3)
- Briefcase log files are now stored in the `logs` subdirectory and only when the current directory is a Briefcase project. (#883)

### Bugfixes

- Output from spawned Python processes, such as when running `briefcase dev`, is no longer buffered and displays in the console immediately. (#891)

### Misc

- \#848, \#885, \#887, \#888, \#889, \#893, \#894, \#895, \#896, \#897, \#899, \#900, \#908, \#909, \#910, \#915

## 0.3.10 (2022-09-28)

### Features

- iOS and Android now supports the installation of binary packages. (#471)
- Apps can now selectively remove files from the final app bundle using the `cleanup_paths` attribute. (#550)
- The Docker image for AppImage builds is created or updated for all commands instead of just `create`. (#796)
- The performance of Briefcase's tool verification process has been improved. (#801)
- Briefcase templates are now versioned by the Briefcase version, rather than the Python version. (#824)
- Android commands now start faster, as they only gather a list of SDK packages when needed to write a log file. (#832)
- Log messages can be captured on iOS if they originate from a dynamically loaded module. (#842)
- Added an "open" command that can be used to open projects in IDEs. (#846)

### Bugfixes

- The Wait Bar is disabled for batch scripts on Windows to prevent hiding user prompts when CTRL+C is pressed. (#811)
- Android emulators that don't provide a model identifier can now be used to launch apps. (#820)
- All `linuxdeploy` plugins are made executable and ELF headers for AppImage plugins are patched for use in `Docker`. (#829)
- The RCEdit plugin can now be upgraded. (#837)
- When verifying the existence of the Android emulator, Briefcase now looks for the actual binary, not the folder that contains the binary. This was causing false positives on some Android SDK setups. (#841)
- When CTRL+C is entered while an external program is running, `briefcase` will properly abort and exit. (#851)
- An issue with running <span class="title-ref">briefcase dev</span> on projects that put their application module in the project root has been resolved. (#863)

### Improved Documentation

- Added FAQ entries on the state of binary package support on mobile. (#471)

### Misc

- \#831, \#834, \#840, \#844, \#857, \#859, \#867, \#868, \#874, \#878, \#879

## 0.3.9 (2022-08-17)

### Features

- Linux apps can now be packaged in Flatpak format. (#359)
- SDKs, tools, and other downloads needed to support app builds are now stored in an OS-native user cache directory instead of `~/.briefcase`. (#374)
- Windows MSI installers can now be configured to ask the user whether they want a per-user or per-machine install. (#382)
- The console output of Windows apps is now captured and displayed during `briefcase run`. (#620)
- Windows apps are now packaged with a stub application. This ensures that Windows apps present with the name and icon of the app, rather than the `pythonw.exe` name and icon. It also allows for improvements in logging and error handling. (#629)
- Temporary docker containers are now cleaned up after use. The wording of Docker progress messages has also been improved. (#774)
- Users can now define a `BRIEFCASE_HOME` environment variable. This allows you to specify the location of the Briefcase tool cache, allowing the user to avoid issues with spaces in paths or disk space limitations. (#789)
- Android emulator output is now printed to the console if it fails to start properly. (#799)
- `briefcase android run` now shows logs from only the current process, and includes all log tags except some particularly noisy and useless ones. It also no longer clears the `logcat` buffer. (#814)

### Bugfixes

- Apps now have better isolation against the current working directory. This ensures that code in the current working directory isn't inadvertently included when an app runs. (#662)
- Windows MSI installers now install in `Program Files`, rather than `Program Files (x86)`. (#688)
- Linuxdeploy plugins can now be used when building Linux AppImages; this resolves many issues with GTK app deployment. (#756)
- Collision protection has been added to custom support packages that have the same name, but are served by different URLs. (#797)
- Python 3.7 and 3.8 on Windows will no longer deadlock when CTRL+C is sent during a subprocess command. (#809)

### Misc

- \#778, \#783, \#784, \#785, \#786, \#787, \#794, \#800, \#805, \#810, \#813, \#815

## 0.3.8 (2022-06-27)

### Features

- macOS apps are now notarized as part of the packaging process. (#365)
- Console output now uses Rich to provide visual highlights and progress bars. (#740)
- The macOS log streamer now automatically exits using the run command when the app exits. (#742)
- A verbose log is written to file when a critical error occurs or --log is specified. (#760)

### Bugfixes

- Updating an Android app now forces a re-install of the app. This corrects a problem (usually seen on physical devices) where app updates wouldn't be deployed if the app was already on the device. (#395)
- The iOS simulator is now able to correctly detect the iOS version when only a device name is provided. (#528)
- Windows MSI projects are now able to support files with non-ASCII filenames. (#749)
- The existence of an appropriate Android system image is now verified independently to the existence of the emulator. (#762)
- The error message presented when the Xcode Command Line Tools are installed, but Xcode is not, has been clarified. (#763)
- The METADATA file generated by Briefcase is now UTF-8 encoded, so it can handle non-Latin-1 characters. (#767)
- Output from subprocesses is correctly encoded, avoiding errors (especially on Windows) when tool output includes non-ASCII content. (#770)

### Improved Documentation

- Documented a workaround for ELF load command address/offset errors seen when using manylinux wheels. (#718)

### Misc

- \#743, \#744, \#755

## 0.3.7 (2022-05-17)

### Features

- Apps can be updated as part of a call to package. (#473)
- The Android emulator can now be used on Apple Silicon hardware. (#616)
- Names that are reserved words in Python (or other common programming languages) are now prevented when creating apps. (#617)
- Names that are invalid on Windows as filenames (such as CON and LPT0) are now invalid as app names. (#685)
- Verbose logging via `-v` and `-vv` now includes the return code, output, and environment variables for shell commands (#704)
- When the output of a wrapped command cannot be parsed, full command output, and failure reason is now logged. (#728)
- The iOS emulator will now run apps natively on Apple Silicon hardware, rather than through Rosetta emulation. (#739)

### Bugfixes

- Bundle identifiers are now validated to ensure they don't contain reserved words. (#460)
- The error reporting when the user is on an unsupported platform or Python version has been improved. (#541)
- When the formal name uses non-Latin characters, the suggested Class and App names are now valid. (#612)
- The code signing process for macOS apps has been made more robust. (#652)
- macOS app binaries are now adhoc signed by default, ensuring they can run on Apple Silicon hardware. (#664)
- Xcode version checks are now more robust. (#668)
- Android projects that have punctuation in their formal names can now build without error. (#696)
- Bundle name validation no longer excludes valid country identifiers (like `in.example`). (#709)
- Application code and dist-info is now fully replaced during an update. (#720)
- Errors related to Java JDK detection now properly contain the value of JAVA_HOME instead of the word None (#727)
- All log entries will now be displayed for the run command on iOS and macOS; previously, initial log entries may have been omitted. (#731)
- Using CTRL+C to stop showing Android emulator logs while running the app will no longer cause the emulator to shutdown. (#733)

### Misc

- \#680, \#681, \#699, \#726, \#734

## 0.3.6 (2022-02-28)

### Features

- On macOS, iOS, and Android, `briefcase run` now displays the application logs once the application has started. (#591)
- Xcode detection code now allows for Xcode to be installed in locations other than `/Applications/Xcode.app`. (#622)
- Deprecated support for Python 3.6. (#653)

### Bugfixes

- Existing app packages are now cleared before reinstalling dependencies. (#644)
- Added binary patch tool for AppImages to increase compatibility. (#667)

### Improved Documentation

- Documentation on creating macOS/iOS code signing identities has been added (#641)

### Misc

- \#587, \#588, \#592, \#598, \#621, \#643, \#654, \#670

## 0.3.5 (2021-03-06)

### Features

- macOS projects can now be generated as an Xcode project. (#523)

### Bugfixes

- macOS apps are now built as an embedded native binary, rather than a shell script invoking a Python script. This was necessary to provide better support for macOS app notarization and sandboxing. (#523)
- Fixed the registration of setuptools entry points caused by a change in case sensitivity handling in Setuptools 53.1.0. (#574)

### Misc

- \#562

## 0.3.4 (2021-01-03)

### Features

- Added signing options for all platforms. App signing is only implemented on macOS, but `--no-sign` can now be used regardless of your target platform. (#486)
- Windows MSI installers can be configured to be per-machine, system-wide installers. (#498)
- Projects can specify a custom branch for the template used to generate the app. (#519)
- Added the <span class="title-ref">--no-run</span> flag to the *dev* command. This allows developers to install app dependencies without running the app. (#522)
- The new project wizard will now warn users when they select a platform that doesn't support mobile deployment. (#539)

### Bugfixes

- Modified the volume mounting process to allow for SELinux. (#500)
- Fixed missing signature for Python executable in macOS app bundle. This enables the packaged dmg to be notarized by Apple. (#514)
- Modified the Windows tests to allow them to pass on 32-bit machines. (#521)
- Fixed a crash when running with verbose output. (#532)

### Improved Documentation

- Clarified documentation around system_requires dependencies on Linux. (#459)

### Misc

- \#465, \#475, \#496, \#512, \#518

## 0.3.3 (2020-07-18)

### Features

- WiX is now auto-downloaded when the MSI backend is used. (#389)
- The `upgrade` command now provides a way to upgrade tools that Briefcase has downloaded, including WiX, Java, Linuxdeploy, and the Android SDK. (#450)

### Bugfixes

- Binary modules in Linux AppImages are now processed correctly, ensuring that no references to system libraries are retained in the AppImage. (#420)
- If pip is configured to use a per-user site_packages, this no longer clashes with the installation of application packages. (#441)
- Docker-using commands now check whether the Docker daemon is running and if the user has permission to access it. (#442)

## 0.3.2 (2020-07-04)

### Features

- Added pytest coverage to CI/CD process. (#417)
- Application metadata now contains a `Briefcase-Version` indicator. (#425)
- The device list returned by `briefcase run android` now uses the Android device model name and unique ID e.g. a Pixel 3a shows up as `Pixel 3a (adbDeviceId)`. (#433)
- Android apps are now packaged in Android App Bundle format. This allows the Play Store to dynamically build the smallest APK appropriate to a device installing an app. (#438)
- PursuedPyBear is now included in the new project wizard. (#440)

### Bugfixes

- iOS builds will now warn if the Xcode command line tools are the active. (#397)
- Linux Docker builds no longer use interactive mode, allowing builds to run on CI (or other TTY-less devices). (#439)

### Improved Documentation

- Documented the process of signing Android apps & publishing them to the Google Play store. (#342)

### Misc

- \#428

## 0.3.1 (2020-06-13)

### Features

- The Linux AppImage backend has been modified to use Docker. This ensures that the AppImage is always built in an environment that is compatible with the support package. It also enables Linux AppImages to be built on macOS and Windows. "Native" builds (i.e., builds that *don't* use Docker) can be invoked using the `--no-docker` argument. (#344)
- A `PYTHONPATH` property has been added to `AppConfig` that describes the `sys.path` changes needed to run the app. (#401)
- Ad-hoc code signing is now possible on macOS with `briefcase package --adhoc-sign`. (#409)
- Android apps can now use use `-` in their bundle name; we now convert `-` to `_` in the resulting Android package identifier and Java package name. (#415)
- Mobile applications now support setting the background color of the splash screen, and setting a build identifier. (#422)
- Android now has a `package` command that produces the release APK. After manually signing this APK, it can be published to the Google Play Store. (#423)

### Bugfixes

- Some stray punctuation in the Android device helper output has been removed. (#396)
- An explicit version check for Docker is now performed. (#402)
- The Linux build process ensures the Docker user matches the UID/GID of the host user. (#403)
- Briefcase now ensures that the Python installation ecosystem tools (`pip`, `setuptools`, and `wheel`), are all present and up to date. (#421)

### Improved Documentation

- Documented that Windows MSI builds produce per-user installable MSI installers, while still supporting per-machine installs via the CLI. (#382)
- `CONTRIBUTING.md` has been updated to link to Briefcase-specific documentation. (#404)
- Removed references to the `build-system` table in `pyproject.toml`. (#410)

### Misc

- \#380, \#384

## 0.3.0 (2020-04-18)

### Features

- Converted Briefcase to be a PEP518 tool, rather than a setuptools extension. (#266)

## 0.2.10  { id="section-26" }

- Improved pre-detection of Xcode and related tools
- Improved error handling when starting external tools
- Fixed iOS simulator integration

## 0.2.9  { id="section-27" }

- Updated mechanism for starting the iOS simulator
- Added support for environment markers in `install_requires`
- Improved error handling when WiX isn't found

## 0.2.8  { id="section-28" }

- Corrects packaging problem with `urllib3`, caused by inconsistency between `requests` and `boto3`.
- Corrected problems with Start menu targets being created on Windows.

## 0.2.7  { id="section-29" }

- Added support for launch images for iPhone X, Xs, Xr, Xs Max and Xr Max
- Completed removal of internal pip API dependencies.

## 0.2.6  { id="section-30" }

- Added support for registering OS-level document type handlers.
- Removed dependency on an internal pip API.
- Corrected invocation of gradlew on Windows
- Addressed support for support builds greater than b9.

## 0.2.5  { id="section-31" }

- Restored download progress bars when downloading support packages.

## 0.2.4  { id="section-32" }

- Corrected a bug in the iOS backend that prevented iOS builds.

## 0.2.3  { id="section-33" }

- Bugfix release, correcting the fix for pip 10 support.

## 0.2.2  { id="section-34" }

- Added compatibility with pip 10.
- Improved Windows packaging to allow for multiple executables
- Added a `--clean` command line option to force a refresh of generated code.
- Improved error handling for bad builds

## 0.2.1  { id="section-35" }

- Improved error reporting when a support package isn't available.

## 0.2.0  { id="section-36" }

- Added `-s` option to launch projects
- Switch to using AWS S3 resources rather than GitHub Files.

## 0.1.9  { id="section-37" }

- Added a full Windows installer backend

## 0.1.8  { id="section-38" }

- Modified template roll out process to avoid API limits on GitHub.

## 0.1.7  { id="section-39" }

- Added check for existing directories, with the option to replace existing content.
- Added a Linux backend.
- Added a Windows backend.
- Added a splash screen for Android

## 0.1.6  { id="section-40" }

- Added a Django backend (`@glasnt`)

## 0.1.5  { id="section-41" }

- Added initial Android template
- Force versions of pip (>= 8.1) and setuptools (>=27.0)
- Drop support for Python 2

## 0.1.4  { id="section-42" }

- Added support for tvOS projects
- Moved to using branches in the project template repositories.

## 0.1.3  { id="section-43" }

- Added support for Android projects using VOC.

## 0.1.2  { id="section-44" }

- Added support for having multi-target support projects. This clears the way for Briefcase to be used for watchOS and tvOS projects, and potentially for Python-OSX-support and Python-iOS-support to be merged into a single Python-Apple-support.

## 0.1.1  { id="section-45" }

- Added support for app icons and splash screens.

## 0.1.0  { id="section-46" }

- Initial public release.
