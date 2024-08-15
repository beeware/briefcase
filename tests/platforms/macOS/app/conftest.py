import os
from pathlib import Path

import pytest

from briefcase.platforms.macOS import SigningIdentity

from ....utils import create_file, create_plist_file


@pytest.fixture
def sekrit_identity():
    return SigningIdentity(id="CAFEBEEF", name="Sekrit identity (DEADBEEF)")


@pytest.fixture
def sekrit_installer_identity():
    return SigningIdentity(id="CAFEFACE", name="Sekrit Installer identity (DEADBEEF)")


@pytest.fixture
def adhoc_identity():
    return SigningIdentity()


@pytest.fixture
def first_app_templated(first_app_config, tmp_path):
    app_path = tmp_path / "base_path/build/first-app/macos/app/First App.app"

    # Create the briefcase.toml file
    create_file(
        tmp_path / "base_path/build/first-app/macos/app/briefcase.toml",
        """
[briefcase]
target_version = "0.3.20"

[paths]
app_packages_path="First App.app/Contents/Resources/app_packages"
support_path="First App.app/Contents/Frameworks"
runtime_path="Python.xcframework/macos-arm64_x86_64/Python.framework"
info_plist_path="First App.app/Contents/Info.plist"
entitlements_path="Entitlements.plist"
""",
    )

    # Create the plist file for the app
    create_plist_file(
        app_path / "Contents/Info.plist",
        {
            "MainModule": "first_app",
        },
    )

    # Create the entitlements file for the app
    create_plist_file(
        tmp_path / "base_path/build/first-app/macos/app/Entitlements.plist",
        {
            "com.apple.security.cs.allow-unsigned-executable-memory": True,
            "com.apple.security.cs.disable-library-validation": True,
        },
    )

    # Create some folders that need to exist.
    (app_path / "Contents/Resources/app_packages").mkdir(parents=True)
    (app_path / "Contents/Frameworks").mkdir(parents=True)

    # Create an installer Distribution.xml
    create_file(
        tmp_path / "base_path/build/first-app/macos/app/installer/Distribution.xml",
        """<?xml?>\n<installer-script></installer-script>""",
    )

    # Select dmg packaging by default
    first_app_config.packaging_format = "dmg"

    return first_app_config


@pytest.fixture
def first_app_with_binaries(first_app_templated, first_app_config, tmp_path):
    app_path = tmp_path / "base_path/build/first-app/macos/app/First App.app"

    # Create the stub binary
    create_file(app_path / "Contents/MacOS/First App", "Stub binary")

    # Create some libraries that need to be signed.
    lib_path = app_path / "Contents/Resources/app_packages"
    frameworks_path = app_path / "Contents/Frameworks"

    for lib in [
        "first_so.so",
        Path("subfolder/second_so.so"),
        "first_dylib.dylib",
        Path("subfolder/second_dylib.dylib"),
        "other_binary",
    ]:
        (lib_path / lib).parent.mkdir(parents=True, exist_ok=True)
        with (lib_path / lib).open("wb") as f:
            f.write(b"\xCA\xFE\xBA\xBEBinary content here")

    # Mach-O file that is executable, with an odd extension
    with (lib_path / "special.binary").open("wb") as f:
        f.write(b"\xCA\xFE\xBA\xBEBinary content here")
    os.chmod(lib_path / "special.binary", 0o755)

    # An embedded app
    (lib_path / "Extras.app/Contents/MacOS").mkdir(parents=True, exist_ok=True)
    with (lib_path / "Extras.app/Contents/MacOS/Extras").open("wb") as f:
        f.write(b"\xCA\xFE\xBA\xBEBinary content here")

    # An embedded framework
    (frameworks_path / "Extras.framework/Resources").mkdir(parents=True, exist_ok=True)
    with (frameworks_path / "Extras.framework/Resources/extras.dylib").open("wb") as f:
        f.write(b"\xCA\xFE\xBA\xBEBinary content here")

    # Make sure there are some files in the bundle that *don't* need to be signed...
    with (lib_path / "first.other").open("w", encoding="utf-8") as f:
        f.write("other")
    with (lib_path / "second.other").open("w", encoding="utf-8") as f:
        f.write("other")

    # A file that has a Mach-O header, but isn't executable
    with (lib_path / "unknown.binary").open("wb") as f:
        f.write(b"\xCA\xFE\xBA\xBEother")

    # A symlink to a Mach-O executable binary file
    (lib_path / "first_symlink.so").symlink_to(lib_path / "first_so.so")

    return first_app_config
