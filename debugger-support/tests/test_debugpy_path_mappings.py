import sys
from pathlib import Path, PosixPath, PurePosixPath, PureWindowsPath, WindowsPath

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


def test_mappings_windows(monkeypatch):
    """Path mappings on an Windows system."""
    # When running tests on Linux/macOS, we have to switch to WindowsPath.
    if isinstance(Path(), PosixPath):
        monkeypatch.setattr(briefcase_debugger.debugpy, "Path", PureWindowsPath)

    config = DebuggerConfig(
        debugger="debugpy",
        host="",
        port=0,
        app_path_mappings=AppPathMappings(
            device_sys_path_regex="app$",
            device_subfolders=["helloworld"],
            host_folders=["src/helloworld"],
        ),
        app_packages_path_mappings=None,
    )

    sys_path = [
        "build\\helloworld\\windows\\app\\src\\python313.zip",
        "build\\helloworld\\windows\\app\\src",
        "build\\helloworld\\windows\\app\\src\\app",
        "build\\helloworld\\windows\\app\\src\\app_packages",
    ]
    monkeypatch.setattr(sys, "path", sys_path)

    path_mappings = briefcase_debugger.debugpy.load_path_mappings(config, False)

    assert path_mappings == [
        # (host_path, device_path)
        ("src/helloworld", "build\\helloworld\\windows\\app\\src\\app\\helloworld"),
    ]


def test_mappings_macos(monkeypatch):
    """Path mappings on an macOS system."""
    # When running tests on windows, we have to switch to PosixPath.
    if isinstance(Path(), WindowsPath):
        monkeypatch.setattr(briefcase_debugger.debugpy, "Path", PurePosixPath)

    config = DebuggerConfig(
        debugger="debugpy",
        host="",
        port=0,
        app_path_mappings=AppPathMappings(
            device_sys_path_regex="app$",
            device_subfolders=["helloworld"],
            host_folders=["src/helloworld"],
        ),
        app_packages_path_mappings=None,
    )

    sys_path = [
        "build/helloworld/macos/app/Hello World.app/Contents/Frameworks/Python.framework/Versions/3.13/lib/python3.13",
        "build/helloworld/macos/app/Hello World.app/Contents/Frameworks/Python.framework/Versions/3.13/lib/python3.13/lib-dynload",
        "build/helloworld/macos/app/Hello World.app/Contents/Resources/app",
        "build/helloworld/macos/app/Hello World.app/Contents/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages",
        "build/helloworld/macos/app/Hello World.app/Contents/Resources/app_packages",
    ]
    monkeypatch.setattr(sys, "path", sys_path)

    path_mappings = briefcase_debugger.debugpy.load_path_mappings(config, False)

    assert path_mappings == [
        # (host_path, device_path)
        (
            "src/helloworld",
            "build/helloworld/macos/app/Hello World.app/Contents/Resources/app/helloworld",
        ),
    ]


def test_mappings_ios(monkeypatch):
    """Path mappings on an iOS system."""
    # When running tests on windows, we have to switch to PosixPath.
    if isinstance(Path(), WindowsPath):
        monkeypatch.setattr(briefcase_debugger.debugpy, "Path", PurePosixPath)

    config = DebuggerConfig(
        debugger="debugpy",
        host="",
        port=0,
        app_path_mappings=AppPathMappings(
            device_sys_path_regex="app$",
            device_subfolders=["helloworld"],
            host_folders=["src/helloworld"],
        ),
        app_packages_path_mappings=AppPackagesPathMappings(
            sys_path_regex="app_packages$",
            host_folder="APP_PACKAGES_PATH/app_packages.iphonesimulator",
        ),
    )

    sys_path = [
        "CoreSimulator/Devices/RANDOM_NUMBER/data/Containers/Bundle/Application/RANDOM_NUMBER/Hello World.app/python/lib/python3.13",
        "CoreSimulator/Devices/RANDOM_NUMBER/data/Containers/Bundle/Application/RANDOM_NUMBER/Hello World.app/python/lib/python3.13/lib-dynload",
        "CoreSimulator/Devices/RANDOM_NUMBER/data/Containers/Bundle/Application/RANDOM_NUMBER/Hello World.app/app",
        "CoreSimulator/Devices/RANDOM_NUMBER/data/Containers/Bundle/Application/RANDOM_NUMBER/Hello World.app/python/lib/python3.13/site-packages",
        "CoreSimulator/Devices/RANDOM_NUMBER/data/Containers/Bundle/Application/RANDOM_NUMBER/Hello World.app/app_packages",
    ]
    monkeypatch.setattr(sys, "path", sys_path)

    path_mappings = briefcase_debugger.debugpy.load_path_mappings(config, False)

    assert path_mappings == [
        # (host_path, device_path)
        (
            "src/helloworld",
            "CoreSimulator/Devices/RANDOM_NUMBER/data/Containers/Bundle/Application/RANDOM_NUMBER/Hello World.app/app/helloworld",
        ),
        (
            "APP_PACKAGES_PATH/app_packages.iphonesimulator",
            "CoreSimulator/Devices/RANDOM_NUMBER/data/Containers/Bundle/Application/RANDOM_NUMBER/Hello World.app/app_packages",
        ),
    ]


def test_mappings_android(monkeypatch):
    """Path mappings on an Android system."""
    # When running tests on windows, we have to switch to PosixPath.
    if isinstance(Path(), WindowsPath):
        monkeypatch.setattr(briefcase_debugger.debugpy, "Path", PurePosixPath)

    config = DebuggerConfig(
        debugger="debugpy",
        host="",
        port=0,
        app_path_mappings=AppPathMappings(
            device_sys_path_regex="app$",
            device_subfolders=["helloworld"],
            host_folders=["src/helloworld"],
        ),
        app_packages_path_mappings=AppPackagesPathMappings(
            sys_path_regex="requirements$",
            host_folder="/BUNDLE_PATH/app/build/python/pip/debug/common",
        ),
    )

    sys_path = [
        "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/app",
        "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/requirements",
        "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/stdlib-x86_64",
        "/data/user/0/com.example.helloworld/files/chaquopy/stdlib-common.imy",
        "/data/user/0/com.example.helloworld/files/chaquopy/bootstrap.imy",
        "/data/user/0/com.example.helloworld/files/chaquopy/bootstrap-native/x86_64",
    ]
    monkeypatch.setattr(sys, "path", sys_path)

    path_mappings = briefcase_debugger.debugpy.load_path_mappings(config, False)

    assert path_mappings == [
        # (host_path, device_path)
        (
            "src/helloworld",
            "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/app/helloworld",
        ),
        (
            "/BUNDLE_PATH/app/build/python/pip/debug/common",
            "/data/data/com.example.helloworld/files/chaquopy/AssetFinder/requirements",
        ),
    ]


def test_mappings_windows_wrong_sys_path(monkeypatch):
    """Path mappings on an Windows system with a wrong sys path set."""
    # When running tests on Linux/macOS, we have to switch to WindowsPath.
    if isinstance(Path(), PosixPath):
        monkeypatch.setattr(briefcase_debugger.debugpy, "Path", PureWindowsPath)

    config = DebuggerConfig(
        debugger="debugpy",
        host="",
        port=0,
        app_path_mappings=AppPathMappings(
            device_sys_path_regex="app$",
            device_subfolders=["helloworld"],
            host_folders=["src/helloworld"],
        ),
        app_packages_path_mappings=None,
    )

    sys_path = []
    monkeypatch.setattr(sys, "path", sys_path)

    with pytest.raises(ValueError):
        briefcase_debugger.debugpy.load_path_mappings(config, False)
