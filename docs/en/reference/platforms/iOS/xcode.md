# iOS XCode project

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

When generating an iOS project, Briefcase produces an XCode project.

## Icon format

iOS projects use `.png` format icons. An application must provide icons
of the following sizes:

- 20px
- 29px
- 40px
- 58px
- 60px
- 76px
- 80px
- 87px
- 120px
- 152px
- 167px
- 180px
- 640px
- 1024px
- 1280px
- 1920px

The icon will also be used to populate the splash screen. You can
specify a background color for the splash screen using the
`splash_background_color` configuration setting.

iOS projects do not support installer images.

## Colors

iOS allows for some customization of the colors used by your app:

- [`splash_background_color`][] is the color
  of the splash background that displays while an app is loading.

## Additional options

The following options can be provided at the command line when producing
iOS projects:

### run

#### `-d <device>` / `--device <device>`

The device simulator to target. Can be either a UDID, a device name
(e.g., `"iPhone 11"`), or a device name and OS version
(`"iPhone 11::iOS 13.3"`).

## Application configuration

### `iOS`

The following options can be added to the
`tool.briefcase.app.<appname>.iOS.app` section of your `pyproject.toml`
file.

### `info`

A property whose sub-attributes define keys that will be added to the
app's `Info.plist` file. Each entry will be converted into a key in the
entitlements file. For example, specifying:

```python
info."UIFileSharingEnabled" = true
```

will result in an `Info.plist` declaration of:

```text
<key>UIFileSharingEnabled</key><true/>
```

Any Boolean or string value can be used for an `Info.plist` value.

### `min_os_version`

The minimum iOS version that the app will support. This controls the
value of `IPHONEOS_DEPLOYMENT_TARGET` used when building the app.

## Permissions

Briefcase cross platform permissions map to the following
[`info`][] keys:

- [`permission.camera`][permissioncamera]: `NSCameraUsageDescription`
- [`permission.microphone`][permissionmicrophone]: `NSMicrophoneUsageDescription`
- [`permission.coarse_location`][permissioncoarse_location]:
  - `NSLocationDefaultAccuracyReduced=True`
  - `NSLocationWhenInUseUsageDescription` if `fine_location` is not defined
- [`permission.fine_location`][permissionfine_location]:
  - `NSLocationDefaultAccuracyReduced=False`
  - `NSLocationWhenInUseUsageDescription`
- [`permission.background_location`][permissionbackground_location]:
  - `NSLocationAlwaysAndWhenInUseUsageDescription`
  - `NSLocationWhenInUseUsageDescription` if neither [`permission.fine_location`][permissionfine_location] or [`permission.coarse_location`][permissioncoarse_location] is set
  - `UIBackgroundModes` will include `location` and `processing`
- [`permission.photo_library`][permissionphoto_library]: `NSPhotoLibraryAddUsageDescription`

## Platform quirks

### Availability of third-party packages  { #ios-third-party-packages }

Briefcase is able to use third-party packages in iOS apps. As long as
the package is available on PyPI, or you can provide a wheel file for
the package, it can be added to the [`requires`][] declaration in your `pyproject.toml` file and used by your
app at runtime.

If the package is pure Python (i.e., it does not contain a binary
library), that's all you need to do. To check whether a package is pure
Python, look at the PyPI downloads page for the project; if the wheels
provided are have a `-py3-none-any.whl` suffix, then they are pure
Python wheels. If the wheels have version and platform-specific
extensions (e.g., `-cp311-cp311-macosx_11_0_universal2.whl`), then the
wheel contains a binary component.

If the package contains a binary component, that wheel needs to be
compiled for iOS. PyPI allows projects to upload iOS-compatible wheels
(identified by suffixes like `-cp314-cp314-ios_15_4_arm64_iphoneos.whl`
or `-cp313-cp313-ios_13_0_x86_64_iphonesimulator.whl`). However, at this
time, most projects do not provide iOS-compatible wheels.

This is expected to improve over time. In the mean time, Briefcase uses
a [secondary repository](https://anaconda.org/beeware/repo) to store
some popular pre-compiled iOS wheels. This repository is maintained by
the BeeWare project, and as a result, it does not have binary wheels for
*every* package that is available on PyPI, or even every *version* of
every package that is on PyPI. If you see the message:

```console
ERROR: Could not find a version that satisfies the requirement <package name> (from versions: none)
ERROR: No matching distribution found for <package name>
```

then the package (or the version that you've specified) probably isn't
supported yet.

It is *usually* possible to compile any binary package wheels for iOS,
depending on the requirements of the package itself. If the package has
a dependency on other binary libraries (e.g., something like `libjpeg`
that isn't written in Python), those libraries will need to be compiled
for iOS as well. However, if the library requires build tools that don't
support iOS, such as a compiler that can't target iOS, or a PEP517 build
system that doesn't support cross-compilation, it may not be possible to
build an iOS wheel.

The recommended way to build iOS-compatible wheels is to use
[cibuildwheel](https://cibuildwheel.pypa.io/en/stable/platforms/#ios).
Despite the name, the tool is not limited to CI environments; it can be
run locally on macOS machines. Many projects already use cibuildwheel to
manage publication of binary wheels. For those projects, it may be
possible to generate iOS wheels by invoking
`cibuildwheel --platform=ios`. Some modifications of the cibuildwheel
configuration may be necessary to provide iOS-specific customizations.

The BeeWare Project also provides the [Mobile
Forge](https://github.com/beeware/mobile-forge) project to assist with
cross-compiling iOS binary wheels for the [secondary package
repository](https://anaconda.org/beeware/repo). This project is mostly
of historical significance; the BeeWare team is now focused on
contributing iOS support upstream, rather than maintaining independent
packaging efforts. If you would like a project to officially support
iOS, you should open a feature request with that project requesting iOS
support, and consider providing a PR to contribute that support.

### Requirements cannot be provided as source tarballs

Briefcase *cannot* install packages published as source tarballs into an
iOS app, even if the package is a pure Python package that would produce
a `py3-none-any` wheel. This is an inherent limitation in the use of
source tarballs as a distribution format.

If you need to install a package in an iOS app that is only published as
a source tarball, you'll need to compile that package into a wheel
first. If the package is pure Python, you can generate a `py3-none-any`
wheel using `pip wheel <package name>`. If the project has a binary
component, you'll need to use
[cibuildwheel](https://cibuildwheel.pypa.io/en/stable/platforms/#ios) or
other similar tooling to compile compatible wheels.

You can then directly add the wheel file to the
[`requires`][] definition for your app, or
put the wheel in a folder and add:

```toml
requirement_installer_args = ["--find-links", "<path-to-wheel-folder>"]
```

to your `pyproject.toml`. This will instruct Briefcase to search that
folder for compatible wheels during the installation process.

### Executable binary content in wheels

The iOS App Store has very stringent constraints on what can be included
in an app bundle, and where it can be included. One of those constraints
is that any executable content must be distributed as a framework, in
the `Frameworks` folder of the iOS project.

Briefcase's app template will process binary wheels to satisfy this
requirement. However, it will only process binary content that is
executable at runtime. Some packages (NumPy is one notable example) are
known to distribute additional executable files, such as statically
linked `.a` libraries, in their wheel content. These files are not
usable at runtime, and Briefcase will not process them. If they're
present in an app bundle at time of submission to the App Store, your
app will not pass app validation, raising errors like:

> Error: Validation failed Invalid bundle structure. The
> `.../libsomething.a` binary file is not permitted. Your app cannot
> contain standalone executables or libraries, other than a valid
> CFBundleExecutable of supported bundles.

To avoid this, you must purge any binary content from your app before
submission. You can do this using the `cleanup_paths` configuration
option:

```python
cleanup_paths = [
    "*/app_packages.*/**/*.a",
]
```

This will find and purge all `.a` content in your app's dependencies.
You can add additional patterns to remove other problematic content.

### Deployment to Simulated and Physical iOS Devices  { #ios-deploy }

Briefcase provides support for deployment to simulated iOS devices
through the command line.

If you want to deploy to a physical iOS device, you will need need to
use XCode through the following steps:

1.  Run `briefcase open ios` in the command line. This will open your
    application in XCode.
2.  Setup your Apple Developer account with your certificate in XCode.
3.  In the project navigator, select your application at the top level
    (the root of the project).
4.  Select the *Signing and Capabilities* tab in the editor area.
5.  Select your Apple Developer team or individual account from the
    *Team* drop-down.
6.  Select your specific device.
7.  Press the run button.
