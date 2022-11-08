import os
from pathlib import Path

import pytest

from ....utils import create_file, create_plist_file


@pytest.fixture
def first_app_with_binaries(first_app_config, tmp_path):
    app_path = tmp_path / "base_path" / "macOS" / "app" / "First App" / "First App.app"

    # Create the briefcase.toml file
    create_file(
        tmp_path / "base_path" / "macOS" / "app" / "First App" / "briefcase.toml",
        """
[paths]
app_packages_path="First App.app/Contents/Resources/app_packages"
support_path="First App.app/Contents/Resources/support"
info_plist_path="First App.app/Contents/Info.plist"
""",
    )

    # Create the plist file for the app
    create_plist_file(
        app_path / "Contents" / "Info.plist",
        {
            "MainModule": "first_app",
        },
    )

    # Create some libraries that need to be signed.
    lib_path = app_path / "Contents" / "Resources"
    for lib in [
        "first_so.so",
        Path("subfolder") / "second_so.so",
        "first_dylib.dylib",
        Path("subfolder") / "second_dylib.dylib",
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
    (lib_path / "Extras.app" / "Contents" / "MacOS").mkdir(parents=True, exist_ok=True)
    with (lib_path / "Extras.app" / "Contents" / "MacOS" / "Extras").open("wb") as f:
        f.write(b"\xCA\xFE\xBA\xBEBinary content here")

    # An embedded framework
    (lib_path / "Extras.framework" / "Resources").mkdir(parents=True, exist_ok=True)
    with (lib_path / "Extras.framework" / "Resources" / "extras.dylib").open("wb") as f:
        f.write(b"\xCA\xFE\xBA\xBEBinary content here")

    # Make sure there are some files in the bundle that *don't* need to be signed...
    with (lib_path / "first.other").open("w") as f:
        f.write("other")
    with (lib_path / "second.other").open("w") as f:
        f.write("other")

    # A file that has a Mach-O header, but isn't executable
    with (lib_path / "unknown.binary").open("wb") as f:
        f.write(b"\xCA\xFE\xBA\xBEother")

    return first_app_config
