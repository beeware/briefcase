import os
import sys

import briefcase_debugger.debugpy
import pytest
from briefcase_debugger.config import (
    AppPackagesPathMappings,
    AppPathMappings,
    DebuggerConfig,
)


def test_mappings_not_existing():
    """Complete empty config."""
    path_mappings = briefcase_debugger.debugpy.load_path_mappings({}, False)
    assert path_mappings == []


def test_mappings_none(monkeypatch):
    """Config with no mappings set."""
    config = DebuggerConfig(
        debugger="debugpy",
        host="",
        port=0,
        app_path_mappings=None,
        app_packages_path_mappings=None,
    )
    path_mappings = briefcase_debugger.debugpy.load_path_mappings(config, False)
    assert path_mappings == []


@pytest.mark.parametrize(
    (
        "os_name",
        "app_path_mappings",
        "app_packages_path_mappings",
        "sys_path",
        "expected_path_mappings",
    ),
    [
        # Windows
        pytest.param(
            "nt",
            AppPathMappings(
                device_sys_path_regex="app$",
                device_subfolders=["helloworld"],
                host_folders=["C:\\PROJECT_ROOT\\src\\helloworld"],
            ),
            None,
            [
                "C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src\\python313.zip",
                "C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src",
                "C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src\\app",
                "C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src\\app_packages",
            ],
            [
                (
                    "C:\\PROJECT_ROOT\\src\\helloworld",
                    "C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src\\app\\helloworld",
                ),
            ],
            id="windows",
        ),
        # Windows with `app_packages_path_mappings`
        # (currently not used by briefcase, but principally possible)
        pytest.param(
            "nt",
            AppPathMappings(
                device_sys_path_regex="app$",
                device_subfolders=["helloworld"],
                host_folders=["C:\\PROJECT_ROOT\\src\\helloworld"],
            ),
            AppPackagesPathMappings(
                sys_path_regex="app_packages$",
                host_folder="C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src\\app_packages",
            ),
            [
                "C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src\\python313.zip",
                "C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src",
                "C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src\\app",
                "C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src\\app_packages",
            ],
            [
                (
                    "C:\\PROJECT_ROOT\\src\\helloworld",
                    "C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src\\app\\helloworld",
                ),
                (
                    "C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src\\app_packages",
                    "C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src\\app_packages",
                ),
            ],
            id="windows-with-app-packages",
        ),
        # macOS
        pytest.param(
            "posix",
            AppPathMappings(
                device_sys_path_regex="app$",
                device_subfolders=["helloworld"],
                host_folders=["/PROJECT_ROOT/src/helloworld"],
            ),
            None,
            [
                "/PROJECT_ROOT/build/helloworld/macos/app/Hello World.app"
                "/Contents/Frameworks/Python.framework/Versions/3.13/lib/python3.13",
                "/PROJECT_ROOT/build/helloworld/macos/app/Hello World.app"
                "/Contents/Frameworks/Python.framework/Versions/3.13"
                "/lib/python3.13/lib-dynload",
                "/PROJECT_ROOT/build/helloworld/macos/app/"
                "Hello World.app/Contents/Resources/app",
                "/PROJECT_ROOT/build/helloworld/macos/app/Hello World.app"
                "/Contents/Frameworks/Python.framework/Versions/3.13"
                "/lib/python3.13/site-packages",
                "/PROJECT_ROOT/build/helloworld/macos/app/"
                "Hello World.app/Contents/Resources/app_packages",
            ],
            [
                (
                    "/PROJECT_ROOT/src/helloworld",
                    "/PROJECT_ROOT/build/helloworld/macos/app/"
                    "Hello World.app/Contents/Resources/app/helloworld",
                )
            ],
            id="macos",
        ),
        # iOS
        pytest.param(
            "posix",
            AppPathMappings(
                device_sys_path_regex="app$",
                device_subfolders=["helloworld"],
                host_folders=["/PROJECT_ROOT/src/helloworld"],
            ),
            AppPackagesPathMappings(
                sys_path_regex="app_packages$",
                host_folder="/APP_PACKAGES_PATH/app_packages.iphonesimulator",
            ),
            [
                "CoreSimulator/Devices/RANDOM_NUMBER/data/Containers/Bundle"
                "/Application/RANDOM_NUMBER/Hello World.app/python/lib/python3.13",
                "CoreSimulator/Devices/RANDOM_NUMBER/data/Containers/Bundle"
                "/Application/RANDOM_NUMBER/Hello World.app/python/lib"
                "/python3.13/lib-dynload",
                "CoreSimulator/Devices/RANDOM_NUMBER/data/Containers/Bundle"
                "/Application/RANDOM_NUMBER/Hello World.app/app",
                "CoreSimulator/Devices/RANDOM_NUMBER/data/Containers/Bundle"
                "/Application/RANDOM_NUMBER/Hello World.app/python/lib"
                "/python3.13/site-packages",
                "CoreSimulator/Devices/RANDOM_NUMBER/data/Containers/Bundle"
                "/Application/RANDOM_NUMBER/Hello World.app/app_packages",
            ],
            [
                (
                    "/PROJECT_ROOT/src/helloworld",
                    "CoreSimulator/Devices/RANDOM_NUMBER/data/Containers/Bundle"
                    "/Application/RANDOM_NUMBER/Hello World.app/app/helloworld",
                ),
                (
                    "/APP_PACKAGES_PATH/app_packages.iphonesimulator",
                    "CoreSimulator/Devices/RANDOM_NUMBER/data/Containers/Bundle"
                    "/Application/RANDOM_NUMBER/Hello World.app/app_packages",
                ),
            ],
            id="ios",
        ),
        # Android (with VS Code running on Windows)
        pytest.param(
            "posix",
            AppPathMappings(
                device_sys_path_regex="app$",
                device_subfolders=["helloworld"],
                host_folders=["C:\\PROJECT_ROOT\\src\\helloworld"],
            ),
            AppPackagesPathMappings(
                sys_path_regex="requirements$",
                host_folder="C:\\BUNDLE_PATH\\app\\build\\python\\pip\\debug\\common",
            ),
            [
                "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/app",
                "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/requirements",
                "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/stdlib-x86_64",
                "/data/user/0/com.example.helloworld/files/chaquopy/stdlib-common.imy",
                "/data/user/0/com.example.helloworld/files/chaquopy/bootstrap.imy",
                "/data/user/0/com.example.helloworld/files/chaquopy/bootstrap-native/x86_64",
            ],
            [
                (
                    "C:\\PROJECT_ROOT\\src\\helloworld",
                    "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/app/helloworld",
                ),
                (
                    "C:\\BUNDLE_PATH\\app\\build\\python\\pip\\debug\\common",
                    "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/requirements",
                ),
            ],
            id="android-on-windows-host",
        ),
        # Android (with VS Code running on POSIX system)
        pytest.param(
            "posix",
            AppPathMappings(
                device_sys_path_regex="app$",
                device_subfolders=["helloworld"],
                host_folders=["/PROJECT_ROOT/src/helloworld"],
            ),
            AppPackagesPathMappings(
                sys_path_regex="requirements$",
                host_folder="/BUNDLE_PATH/app/build/python/pip/debug/common",
            ),
            [
                "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/app",
                "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/requirements",
                "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/stdlib-x86_64",
                "/data/user/0/com.example.helloworld/files/chaquopy/stdlib-common.imy",
                "/data/user/0/com.example.helloworld/files/chaquopy/bootstrap.imy",
                "/data/user/0/com.example.helloworld/files/chaquopy/bootstrap-native/x86_64",
            ],
            [
                (
                    "/PROJECT_ROOT/src/helloworld",
                    "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/app/helloworld",
                ),
                (
                    "/BUNDLE_PATH/app/build/python/pip/debug/common",
                    "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/requirements",
                ),
            ],
            id="android-on-posix-host",
        ),
    ],
)
def test_mappings(
    os_name: str,
    app_path_mappings: AppPathMappings,
    app_packages_path_mappings: AppPackagesPathMappings | None,
    sys_path: list[str],
    expected_path_mappings: list[tuple[str, str]],
    monkeypatch,
):
    if os.name != os_name:
        pytest.skip(f"Test only runs on {os_name} systems")

    config = DebuggerConfig(
        debugger="debugpy",
        host="",
        port=0,
        app_path_mappings=app_path_mappings,
        app_packages_path_mappings=app_packages_path_mappings,
    )

    monkeypatch.setattr(sys, "path", sys_path)

    path_mappings = briefcase_debugger.debugpy.load_path_mappings(config, False)

    assert path_mappings == expected_path_mappings


@pytest.mark.parametrize(
    ("os_name", "app_path_mappings"),
    [
        # Windows
        pytest.param(
            "nt",
            AppPathMappings(
                device_sys_path_regex="app$",
                device_subfolders=["helloworld"],
                host_folders=["C:\\PROJECT_ROOT\\src\\helloworld"],
            ),
            id="windows",
        ),
        # POSIX (macOS/iOS/Android)
        pytest.param(
            "posix",
            AppPathMappings(
                device_sys_path_regex="app$",
                device_subfolders=["helloworld"],
                host_folders=["/PROJECT_ROOT/src/helloworld"],
            ),
            id="posix",
        ),
    ],
)
def test_mappings_wrong_sys_path(
    os_name: str,
    app_path_mappings: AppPathMappings,
    monkeypatch,
):
    """Path mappings with a wrong sys path set."""
    if os.name != os_name:
        pytest.skip(f"Test only runs on {os_name} systems")

    config = DebuggerConfig(
        debugger="debugpy",
        host="",
        port=0,
        app_path_mappings=app_path_mappings,
        app_packages_path_mappings=None,
    )

    sys_path = []
    monkeypatch.setattr(sys, "path", sys_path)

    with pytest.raises(ValueError, match=r"No sys.path entry matches regex"):
        briefcase_debugger.debugpy.load_path_mappings(config, False)
