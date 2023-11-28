import os
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.console import LogLevel
from briefcase.exceptions import BriefcaseCommandError, UnsupportedHostError
from briefcase.integrations import windows_sdk
from briefcase.integrations.windows_sdk import WindowsSDK


@pytest.fixture
def mock_winreg(monkeypatch):
    """Mock out winreg module."""
    winreg = MagicMock()
    monkeypatch.setattr(windows_sdk, "winreg", winreg)

    # Default all registry reads to "key doesn't exist"
    winreg.OpenKeyEx.side_effect = MagicMock()
    winreg.QueryValueEx.side_effect = FileNotFoundError

    # Initialize necessary but inconsequential winreg constants for testing
    winreg.KEY_READ = 131097
    winreg.KEY_WOW64_32KEY = 512
    winreg.KEY_WOW64_64KEY = 256
    winreg.HKEY_LOCAL_MACHINE = "HKEY_LOCAL_MACHINE"
    winreg.HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
    winreg.REG_SZ = 1

    return winreg


def setup_winsdk_install(
    base_path: Path,
    version: str,
    arch="x64",
    skip_bins=False,
) -> (Path, str):
    """Create a mock Windows SDK for the version and arch.

    :param base_path: base path to create the SDK in; should be pytest's tmp_path.
    :param version: SDK version triple, e.g. 1.2.3. The created directory path will include
        a servicing version of 0, e.g. base_path/win_sdk/1.2.3.0.
    :param arch: The architecture for the SDK, e.g. amd64 or arm64.
    :param skip_bins: Do not create mock binaries in `bin` directory.
    :returns: tuple of path to base of SDK install and version triple
    """
    sdk_path = base_path / "win_sdk"
    sdk_ver = version
    (sdk_path / "bin" / f"{sdk_ver}.0" / arch).mkdir(parents=True, exist_ok=True)
    # Mock the necessary tools in the SDK
    if not skip_bins:
        (sdk_path / "bin" / f"{sdk_ver}.0" / arch / "signtool.exe").touch()
    return sdk_path, sdk_ver


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.windows_sdk = "tool"

    tool = WindowsSDK.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.windows_sdk


@pytest.mark.parametrize("host_os", ["Darwin", "Linux", "wonky"])
def test_unsupported_os(mock_tools, host_os):
    """When host OS is not supported, an error is raised."""
    mock_tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match=f"{WindowsSDK.name} is not supported on {host_os}",
    ):
        WindowsSDK.verify(mock_tools)


@pytest.mark.parametrize(
    "host_arch, sdk_arch", [("AMD64", "x64"), ("ARM64", "arm64"), ("gothic", "gothic")]
)
def test_winsdk_arch(
    mock_tools,
    mock_winreg,
    host_arch,
    sdk_arch,
    tmp_path,
    monkeypatch,
):
    """The architecture of the host machine is respected."""
    # Mock the environment for a Windows SDK install
    sdk_path, sdk_ver = setup_winsdk_install(tmp_path, "1.1.1", sdk_arch)

    # Patch target SDK version
    monkeypatch.setattr(WindowsSDK, "SDK_VERSION", "1.1")
    monkeypatch.setattr(WindowsSDK, "SDK_MIN_VERSION", 0)

    # Mock lookup of Windows SDK
    mock_sdks = MagicMock(spec=WindowsSDK._windows_sdks)
    mock_sdks.return_value = [(sdk_path, f"{sdk_ver}.0")]
    monkeypatch.setattr(WindowsSDK, "_windows_sdks", mock_sdks)

    # Mock the machine
    mock_tools.host_arch = host_arch

    # Verify the install
    win_sdk = WindowsSDK.verify(mock_tools)

    # The returned paths are as expected (and are the full paths)
    signtool_path = tmp_path / "win_sdk/bin/1.1.1.0" / sdk_arch / "signtool.exe"
    assert win_sdk.signtool_exe == signtool_path


def test_winsdk_valid_env_vars(mock_tools, mock_winreg, tmp_path, monkeypatch):
    """If the WindowsSDKDir and WindowsSDKVersion env vars point to a suitable Windows
    SDK install, the validator succeeds."""
    # Mock the environment for a Windows SDK install
    sdk_path, sdk_ver = setup_winsdk_install(tmp_path, "1.1.1", "x64")

    # Patch target SDK version
    monkeypatch.setattr(WindowsSDK, "SDK_VERSION", "1.1")
    monkeypatch.setattr(WindowsSDK, "SDK_MIN_VERSION", 0)

    # Set up environment variables for SDK location
    mock_tools.os.environ = {
        "WindowsSDKDir": os.fsdecode(sdk_path),
        "WindowsSDKVersion": f"{sdk_ver}.0",
    }

    # Verify the install
    win_sdk = WindowsSDK.verify(mock_tools)

    # The returned paths are as expected (and are the full paths)
    signtool_path = tmp_path / "win_sdk/bin/1.1.1.0/x64/signtool.exe"
    assert win_sdk.signtool_exe == signtool_path


def test_winsdk_invalid_env_vars(mock_tools, mock_winreg, tmp_path, monkeypatch):
    """If the WindowsSDKDir and WindowsSDKVersion env vars point to an invalid Windows
    SDK install, the validator fails."""
    # Mock the environment for a Windows SDK install
    sdk_path = tmp_path / "win_sdk"
    sdk_ver = "1.1.1.0"

    # Patch target SDK version
    monkeypatch.setattr(WindowsSDK, "SDK_VERSION", "1.1")
    monkeypatch.setattr(WindowsSDK, "SDK_MIN_VERSION", 0)

    # Set up environment variables for SDK location
    mock_tools.os.environ = {
        "WindowsSDKDir": os.fsdecode(sdk_path),
        "WindowsSDKVersion": f"{sdk_ver}.0",
    }

    # Fail validation for missing install from env vars
    with pytest.raises(
        BriefcaseCommandError,
        match="The 'WindowsSDKDir' and 'WindowsSDKVersion' environment variables do not point",
    ):
        WindowsSDK.verify(mock_tools)


def test_winsdk_latest_install_from_reg(mock_tools, mock_winreg, tmp_path, monkeypatch):
    """If the first (i.e. "latest") version of the SDK found in the registry is valid,
    the validator succeeds."""
    # Bypass using SDK in env vars
    mock_tools.os.environ.get.return_value = None

    # Turn on verbose logging
    mock_tools.logger.verbosity = LogLevel.DEBUG

    # Patch target SDK version
    monkeypatch.setattr(WindowsSDK, "SDK_VERSION", "83.0")
    monkeypatch.setattr(WindowsSDK, "SDK_MIN_VERSION", 0)

    # Mock the SDK install
    sdk_path, sdk_ver = setup_winsdk_install(tmp_path, "83.0.1")

    # Return "latest" SDK as first match
    mock_winreg.QueryValueEx.side_effect = [
        (str(sdk_path), mock_winreg.REG_SZ),
        (sdk_ver, mock_winreg.REG_SZ),
    ]

    # Verify the install
    win_sdk = WindowsSDK.verify(mock_tools)

    # The environment was queried.
    mock_tools.os.environ.get.assert_called_once_with("WindowsSDKDir")

    # The returned paths are as expected (and are the full paths)
    signtool_path = tmp_path / "win_sdk/bin/83.0.1.0/x64/signtool.exe"
    assert win_sdk.signtool_exe == signtool_path


def test_winsdk_nonlatest_install_from_reg(
    mock_tools,
    mock_winreg,
    tmp_path,
    capsys,
    monkeypatch,
):
    """If a subsequent version of the SDK found in the registry is valid, the validator
    succeeds."""
    # Bypass using SDK in env vars
    mock_tools.os.environ.get.return_value = None

    # Turn on verbose logging
    mock_tools.logger.verbosity = LogLevel.DEBUG

    # Patch target SDK version
    monkeypatch.setattr(WindowsSDK, "SDK_VERSION", "85.0")
    monkeypatch.setattr(WindowsSDK, "SDK_MIN_VERSION", 0)

    # Set up an SDK installation without expected binaries
    WindowsSDK.SDK_VERSION = "85.0"
    invalid_sdk_path, invalid_sdk_ver = setup_winsdk_install(
        tmp_path / "invalid", "85.0.9", skip_bins=True
    )

    # Mock the SDK install to be used
    sdk_path, sdk_ver = setup_winsdk_install(tmp_path, "85.0.8")

    # Mock the registry queries via QueryValueEx
    mock_winreg.QueryValueEx.side_effect = [
        (str(invalid_sdk_path), mock_winreg.REG_SZ),
        (invalid_sdk_ver, mock_winreg.REG_SZ),
        (str(sdk_path), mock_winreg.REG_SZ),
        (sdk_ver, mock_winreg.REG_SZ),
    ]

    # Verify the install
    win_sdk = WindowsSDK.verify(mock_tools)

    # Confirm invalid SDK was evaluated
    expected_output = (
        "\n"
        "[Windows SDK] Finding Suitable Installation...\n"
        f"Evaluating Registry SDK version '85.0.9.0' at {tmp_path / 'invalid' / 'win_sdk'}\n"
        f"Evaluating Registry SDK version '85.0.8.0' at {tmp_path / 'win_sdk'}\n"
        f"Using Windows SDK v85.0.8.0 at {tmp_path / 'win_sdk'}\n"
    )
    assert capsys.readouterr().out == expected_output

    # The returned paths are as expected (and are the full paths)
    signtool_path = tmp_path / "win_sdk/bin/85.0.8.0/x64/signtool.exe"
    assert win_sdk.signtool_exe == signtool_path


@pytest.mark.parametrize(
    "reg_installs, additional_installs",
    [
        # One invalid registry install; no additional installs
        [[("invalid_1", "85.0.1")], []],
        # One invalid registry install with missing SDK version; no additional installs
        [[("invalid_1", "")], []],
        # One invalid registry install but directory key lookup fails; no additional installs
        [[("invalid_1", "85.0.1"), (FileNotFoundError, "")], []],
        # One invalid registry install but version key lookup fails; no additional installs
        [[("invalid_1", "85.0.1"), ("invalid_1", FileNotFoundError)], []],
        # Multiple invalid registry installs; no additional installs
        [[("invalid_1", "85.0.1"), ("invalid_2", "85.0.2")], []],
        [[("invalid_1", "85.0.0"), ("invalid_2", "86.0.2")], []],
        # One invalid registry install; one additional invalid install
        [[("invalid_2", "85.0.1")], [("invalid_2", "85.0.2")]],
        # One invalid registry install; multiple additional invalid installs
        [[("invalid_3", "85.0.1")], [("invalid_3", "85.0.3"), ("invalid_3", "85.0.2")]],
        [[("invalid_3", "")], [("invalid_3", "85.0.3"), ("invalid_3", "85.0.2")]],
        # Multiple invalid registry installs; one additional install
        [[("invalid_4", "85.0.1"), ("invalid_5", "85.0.3")], [("invalid_5", "85.0.4")]],
        [
            [("invalid_4", FileNotFoundError), ("invalid_5", "85.0.3")],
            [("invalid_5", "85.0.4")],
        ],
        [[(FileNotFoundError, ""), ("invalid_5", "85.0.3")], [("invalid_5", "85.0.4")]],
    ],
)
def test_winsdk_invalid_install_from_reg(
    mock_tools,
    mock_winreg,
    reg_installs,
    additional_installs,
    tmp_path,
    capsys,
    monkeypatch,
):
    """If none of the SDKs found in the registry are valid, the validator fails."""
    # Bypass using SDK in env vars
    mock_tools.os.environ.get.return_value = None

    # Bypass using default SDK dirs
    WindowsSDK.DEFAULT_SDK_DIRS = []

    # Turn on verbose logging
    mock_tools.logger.verbosity = LogLevel.DEBUG

    # Patch target SDK version
    monkeypatch.setattr(WindowsSDK, "SDK_VERSION", "85.0")
    monkeypatch.setattr(WindowsSDK, "SDK_MIN_VERSION", 1)

    # Set up SDK installations without expected binaries
    reg_queries = []
    for subdir, version in reg_installs:
        reg_queries.extend(
            setup_winsdk_install(tmp_path / subdir, version, skip_bins=True)
            if FileNotFoundError not in {subdir, version}
            else [subdir, version]
        )
    for subdir, version in additional_installs:
        setup_winsdk_install(tmp_path / subdir, version, skip_bins=True)
    # Add enough exceptions to run out any remaining registry reads
    reg_queries.extend([FileNotFoundError] * 12)

    # Mock the registry queries for install dir and version
    mock_winreg.QueryValueEx.side_effect = [
        (q, mock_winreg.REG_SZ) if q is not FileNotFoundError else FileNotFoundError
        for q in reg_queries
    ]

    # Verify the install
    error_text = (
        "Unable to locate a suitable Windows SDK v85.0 installation.\n"
        "\n"
        "Ensure at least v85.0.1.0 is installed and the components below are included:\n"
        "\n"
        "    * Windows SDK Signing Tools for Desktop Apps\n"
        "    * Windows SDK for UWP Managed Apps\n"
        "\n"
        "See https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/ to install the SDK.\n"
    )
    with pytest.raises(BriefcaseCommandError, match=re.escape(error_text)):
        WindowsSDK.verify(mock_tools)

    # Confirm invalid SDK was evaluated
    expected_output = "\n[Windows SDK] Finding Suitable Installation...\n"
    for subdir, version in [t for t in reg_installs if FileNotFoundError not in t]:
        if subdir and version:
            sdk_path = tmp_path / subdir / "win_sdk"
            expected_output += (
                f"Evaluating Registry SDK version '{version}.0' at {sdk_path}\n"
            )
    for subdir, version in additional_installs:
        sdk_path = tmp_path / subdir / "win_sdk"
        expected_output += (
            f"Evaluating Registry SDK Bin version '{version}.0' at {sdk_path}\n"
        )
    assert capsys.readouterr().out == expected_output


def test_winsdk_valid_install_from_default_dir(
    mock_tools,
    mock_winreg,
    tmp_path,
    capsys,
    monkeypatch,
):
    """If an SDKs in a default directory is valid, the validator succeeds."""
    # Bypass using SDK in env vars
    mock_tools.os.environ.get.return_value = None

    # Turn on verbose logging
    mock_tools.logger.verbosity = LogLevel.DEBUG

    # Patch target SDK version
    monkeypatch.setattr(WindowsSDK, "SDK_VERSION", "86.0")
    monkeypatch.setattr(WindowsSDK, "SDK_MIN_VERSION", 0)

    # Set up SDK installations
    sdk_dir, _ = setup_winsdk_install(tmp_path, "86.0.8")
    invalid_sdk_path, _ = setup_winsdk_install(
        tmp_path / "invalid", "86.0.7", skip_bins=True
    )
    WindowsSDK.DEFAULT_SDK_DIRS = [invalid_sdk_path, sdk_dir]

    # Verify the install
    win_sdk = WindowsSDK.verify(mock_tools)

    # Confirm invalid SDK was evaluated
    expected_output = (
        "\n"
        "[Windows SDK] Finding Suitable Installation...\n"
        f"Evaluating Default Bin SDK version '86.0.7.0' at {tmp_path / 'invalid' / 'win_sdk'}\n"
        f"Evaluating Default Bin SDK version '86.0.8.0' at {tmp_path / 'win_sdk'}\n"
        f"Using Windows SDK v86.0.8.0 at {tmp_path / 'win_sdk'}\n"
    )
    assert capsys.readouterr().out == expected_output

    # The returned paths are as expected (and are the full paths)
    signtool_path = tmp_path / "win_sdk/bin/86.0.8.0/x64/signtool.exe"
    assert win_sdk.signtool_exe == signtool_path


def test_winsdk_invalid_install_from_default_dir(
    mock_tools,
    mock_winreg,
    tmp_path,
    capsys,
    monkeypatch,
):
    """If none of the SDKs in the default directories are valid, the validator fails."""
    # Bypass using SDK in env vars
    mock_tools.os.environ.get.return_value = None

    # Turn on verbose logging
    mock_tools.logger.verbosity = LogLevel.DEBUG

    # Patch target SDK version
    monkeypatch.setattr(WindowsSDK, "SDK_VERSION", "87.0")
    monkeypatch.setattr(WindowsSDK, "SDK_MIN_VERSION", 0)

    # Set up SDK installations
    invalid_sdk_path_1, _ = setup_winsdk_install(
        tmp_path / "invalid_1", "87.0.7", skip_bins=True
    )
    invalid_sdk_path_2, _ = setup_winsdk_install(
        tmp_path / "invalid_2", "87.0.8", skip_bins=True
    )
    WindowsSDK.DEFAULT_SDK_DIRS = [
        tmp_path / "nonexistent_dir",
        invalid_sdk_path_1,
        invalid_sdk_path_2,
    ]

    # Verify the install
    with pytest.raises(
        BriefcaseCommandError,
        match="Unable to locate a suitable Windows SDK v87.0 installation.",
    ):
        WindowsSDK.verify(mock_tools)

    # Confirm invalid SDK was evaluated
    expected_output = (
        "\n"
        "[Windows SDK] Finding Suitable Installation...\n"
        f"Evaluating Default Bin SDK version '87.0.7.0' at {tmp_path / 'invalid_1' / 'win_sdk'}\n"
        f"Evaluating Default Bin SDK version '87.0.8.0' at {tmp_path / 'invalid_2' / 'win_sdk'}\n"
    )
    assert capsys.readouterr().out == expected_output
