import os
from pathlib import Path

import pytest

from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.parametrize(
    "host_os, name",
    [
        ("windows", "win"),
        ("Windows", "win"),
        ("darwin", "mac"),
        ("Darwin", "mac"),
    ],
)
def test_cmdline_tools_url(mock_tools, android_sdk, host_os, name):
    """Validate that the SDK URL is computed using `host_os`."""
    mock_tools.host_os = host_os

    assert android_sdk.cmdline_tools_url == (
        f"https://dl.google.com/android/repository/commandlinetools-{name}-8092744_latest.zip"
    )


@pytest.mark.parametrize(
    "host_os, sdkmanager_name",
    [("Windows", "sdkmanager.bat"), ("NonWindows", "sdkmanager")],
)
def test_sdkmanager_path(mock_tools, android_sdk, host_os, sdkmanager_name):
    """Validate that if the user is on Windows, we run `sdkmanager.bat`,
    otherwise, `sdkmanager`."""
    # Mock out `host_os` so we can test Windows when not on Windows.
    mock_tools.host_os = host_os

    assert android_sdk.sdkmanager_path == (
        android_sdk.root_path / "cmdline-tools" / "latest" / "bin" / sdkmanager_name
    )


@pytest.mark.parametrize(
    "host_os, adb_name",
    [("Windows", "adb.exe"), ("NonWindows", "adb")],
)
def test_adb_path(mock_tools, android_sdk, host_os, adb_name):
    """Validate that if the user is on Windows, we run `adb.bat`, otherwise,
    `adb`."""
    # Mock out `host_os` so we can test Windows when not on Windows.
    mock_tools.host_os = host_os

    assert android_sdk.adb_path == (android_sdk.root_path / "platform-tools" / adb_name)


@pytest.mark.parametrize(
    "host_os, avdmanager_name",
    [("Windows", "avdmanager.bat"), ("NonWindows", "avdmanager")],
)
def test_avdmanager_path(mock_tools, android_sdk, host_os, avdmanager_name):
    """Validate that if the user is on Windows, we run `avdmanager.bat`,
    otherwise, `avdmanager`."""
    # Mock out `host_os` so we can test Windows when not on Windows.
    mock_tools.host_os = host_os

    assert android_sdk.avdmanager_path == (
        android_sdk.root_path / "cmdline-tools" / "latest" / "bin" / avdmanager_name
    )


@pytest.mark.parametrize(
    "host_os, emulator_name",
    [("Windows", "emulator.exe"), ("NonWindows", "emulator")],
)
def test_emulator_path(mock_tools, android_sdk, host_os, emulator_name):
    """Validate that if the user is on Windows, we run `emulator.bat`,
    otherwise, `emulator`."""
    # Mock out `host_os` so we can test Windows when not on Windows.
    mock_tools.host_os = host_os

    assert android_sdk.emulator_path == (
        android_sdk.root_path / "emulator" / emulator_name
    )


def test_avd_path(mock_tools, android_sdk, tmp_path):
    assert android_sdk.avd_path == tmp_path / "home" / ".android" / "avd"


def test_simple_env(mock_tools, android_sdk, tmp_path):
    """The SDK Environment can be constructed."""
    assert android_sdk.env == {
        "JAVA_HOME": os.fsdecode(Path("/path/to/jdk")),
        "ANDROID_SDK_ROOT": os.fsdecode(tmp_path / "sdk"),
    }


def test_managed_install(mock_tools, android_sdk):
    """All Android SDK installs are managed."""
    assert android_sdk.managed_install


@pytest.mark.parametrize(
    "host_os, host_arch, emulator_abi",
    [
        ("Darwin", "x86_64", "x86_64"),
        ("Darwin", "arm64", "arm64-v8a"),
        ("Windows", "x86_64", "x86_64"),
        ("Windows", "AMD64", "x86_64"),
        ("Linux", "x86_64", "x86_64"),
    ],
)
def test_emulator_abi(mock_tools, android_sdk, host_os, host_arch, emulator_abi):
    """The emulator API can be determined from the host OS and architecture."""
    # Mock the hardware and operating system
    mock_tools.host_os = host_os
    mock_tools.host_arch = host_arch

    assert android_sdk.emulator_abi == emulator_abi


@pytest.mark.parametrize(
    "host_os, host_arch",
    [
        ("Darwin", "powerpc"),
        ("Windows", "arm64"),
        ("Windows", "powerpc"),
        ("Linux", "arm64"),
        ("Linux", "powerpc"),
    ],
)
def test_bad_emulator_abi(mock_tools, android_sdk, host_os, host_arch):
    """If the host OS/architecture isn't supported by Android, an error is
    raised."""
    # Mock the hardware and operating system
    mock_tools.host_os = host_os
    mock_tools.host_arch = host_arch

    with pytest.raises(
        BriefcaseCommandError,
        match=rf"The Android emulator does not currently support {host_os} {host_arch} hardware.",
    ):
        android_sdk.emulator_abi


def test_adb_for_device(mock_tools, android_sdk):
    "An ADB instance can be bound to a device."
    adb = android_sdk.adb("some-device")

    assert adb.tools == mock_tools
    assert adb.device == "some-device"
