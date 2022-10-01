import os
from pathlib import Path

import pytest


@pytest.fixture
def first_app_with_binaries(first_app_config, tmp_path):
    # Create some libraries that need to be signed.
    app_path = tmp_path / "base_path" / "macOS" / "app" / "First App" / "First App.app"
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
