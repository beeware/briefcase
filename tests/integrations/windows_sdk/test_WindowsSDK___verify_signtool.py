import subprocess

import pytest

from briefcase.integrations.windows_sdk import WindowsSDK

from .test_WindowsSDK__verify import setup_winsdk_install


@pytest.fixture
def windows_sdk(mock_tools, tmp_path, monkeypatch) -> WindowsSDK:
    # Patch target SDK version
    monkeypatch.setattr(WindowsSDK, "SDK_VERSION", "83.0")
    monkeypatch.setattr(WindowsSDK, "SDK_MIN_VERSION", 0)

    yield WindowsSDK(
        tools=mock_tools,
        root_path=tmp_path / "win_sdk",
        version="83.1.0.0",
        arch="x64",
    )


def test_winsdk_signtool_succeeds(windows_sdk, tmp_path):
    """Validation succeeds if signtool exists and can be run."""
    setup_winsdk_install(
        base_path=tmp_path,
        version=".".join(windows_sdk.version.split(".")[0:3]),
        arch="x64",
    )

    assert WindowsSDK._verify_signtool(windows_sdk) is True


def test_winsdk_signtool_does_not_exist(windows_sdk):
    """Validation fails if signtool does not exist."""
    assert WindowsSDK._verify_signtool(windows_sdk) is False


def test_winsdk_signtool_raises_oserror(windows_sdk, tmp_path):
    """Validation fails if running signtool raises a OSError."""
    setup_winsdk_install(
        base_path=tmp_path,
        version=".".join(windows_sdk.version.split(".")[0:3]),
        arch="x64",
    )
    windows_sdk.tools.subprocess.check_output.side_effect = OSError(
        14001,
        " The application has failed to start because its side-by-side configuration is incorrect.",
    )

    assert WindowsSDK._verify_signtool(windows_sdk) is False


def test_winsdk_signtool_raises_calledprocesserror(windows_sdk, tmp_path):
    """Validation fails if running signtool raises a OSError."""
    setup_winsdk_install(
        base_path=tmp_path,
        version=".".join(windows_sdk.version.split(".")[0:3]),
        arch="x64",
    )
    windows_sdk.tools.subprocess.check_output.side_effect = (
        subprocess.CalledProcessError(
            returncode=1,
            cmd="signtool.exe -?",
            output="Unknown error",
        )
    )

    assert WindowsSDK._verify_signtool(windows_sdk) is False
