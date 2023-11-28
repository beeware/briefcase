import os
from pathlib import Path

import pytest

from ....utils import create_file, create_plist_file


@pytest.fixture
def first_app_templated(first_app_config, tmp_path):
    app_path = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "app"
        / "First App.app"
    )

    # Create the briefcase.toml file
    create_file(
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "app"
        / "briefcase.toml",
        """
[paths]
app_packages_path="First App.app/Contents/Resources/app_packages"
support_path="First App.app/Contents/Resources/support"
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
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "app"
        / "Entitlements.plist",
        {
            "com.apple.security.cs.allow-unsigned-executable-memory": True,
            "com.apple.security.cs.disable-library-validation": True,
        },
    )

    # Create some folders that need to exist.
    (app_path / "Contents/Resources/app_packages").mkdir(parents=True)
    (app_path / "Contents/Frameworks").mkdir(parents=True)

    # Select dmg packaging by default
    first_app_config.packaging_format = "dmg"

    return first_app_config


@pytest.fixture
def first_app_with_binaries(first_app_templated, first_app_config, tmp_path):
    app_path = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "app"
        / "First App.app"
    )

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

    return first_app_config
