import pytest

from briefcase.integrations.windows_sdk import WindowsSDK


@pytest.fixture
def windows_sdk(mock_tools, tmp_path):
    return WindowsSDK(
        mock_tools,
        root_path=tmp_path,
        version="10.0.19000.0",
        arch="x64",
    )


def test_managed_install(windows_sdk):
    """All Windows SDK installs are unmanaged."""
    assert windows_sdk.managed_install is False


@pytest.mark.parametrize("sdk_arch", ["x64", "arm64", "gothic"])
def test_paths(windows_sdk, tmp_path, sdk_arch):
    """Windows SDK paths are appropriate for arch and version."""
    windows_sdk.arch = sdk_arch

    expected_bin_path = tmp_path / "bin/10.0.19000.0" / sdk_arch
    assert windows_sdk.bin_path == expected_bin_path
    assert windows_sdk.signtool_exe == expected_bin_path / "signtool.exe"
