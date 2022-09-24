import pytest

from briefcase.exceptions import MissingToolError, NetworkFailure
from briefcase.integrations.linuxdeploy import LinuxDeployBase
from tests.integrations.linuxdeploy.utils import (
    side_effect_create_mock_appimage,
    side_effect_create_mock_tool,
)


class LinuxDeployDummy(LinuxDeployBase):
    name = "dummy-plugin"
    full_name = "Dummy plugin"
    install_msg = "Installing dummy plugin"

    def __init__(self, command, file_name="linuxdeploy-dummy-wonky.AppImage", **kwargs):
        super().__init__(command)
        self._file_name = file_name
        self.kwargs = kwargs

    @property
    def file_name(self):
        return self._file_name

    @property
    def download_url(self):
        return f"https://example.com/path/to/{self._file_name}"

    @property
    def file_path(self):
        return self.tools.base_path / "somewhere"


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.linuxdeploy = "tool"

    tool = LinuxDeployBase.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.linuxdeploy


def test_verify_exists(mock_tools, tmp_path):
    """If the tool/plugin already exists, verification doesn't download."""
    appimage_path = (
        tmp_path / "tools" / "somewhere" / "linuxdeploy-dummy-wonky.AppImage"
    )

    # Mock the existence of an install
    appimage_path.parent.mkdir(parents=True)
    appimage_path.touch()

    # Create a linuxdeploy wrapper by verification
    linuxdeploy = LinuxDeployDummy.verify(mock_tools)

    # No download occurred
    assert mock_tools.download.file.call_count == 0
    assert mock_tools.os.chmod.call_count == 0

    # The build command retains the path to the downloaded file.
    assert linuxdeploy.file_path == appimage_path.parent


def test_verify_does_not_exist_dont_install(mock_tools):
    """If the tool/plugin doesn't exist, and install=False, it is *not*
    downloaded."""
    # True to create a linuxdeploy wrapper by verification.
    # This will fail because it doesn't exist, but installation was disabled.
    with pytest.raises(MissingToolError):
        LinuxDeployDummy.verify(mock_tools, install=False)

    # No download occurred
    assert mock_tools.download.file.call_count == 0
    assert mock_tools.os.chmod.call_count == 0


def test_verify_does_not_exist(mock_tools, tmp_path):
    """If the tool/plugin doesn't exist, it is downloaded."""
    appimage_path = (
        tmp_path / "tools" / "somewhere" / "linuxdeploy-dummy-wonky.AppImage"
    )

    # Mock a successful download
    mock_tools.download.file.side_effect = side_effect_create_mock_appimage(
        appimage_path
    )

    # Create a linuxdeploy wrapper by verification, with some extra args
    linuxdeploy = LinuxDeployDummy.verify(mock_tools, arg1="value1", arg2="value2")

    # The extra verification arguments were passed to the tool instance
    assert linuxdeploy.kwargs == {
        "arg1": "value1",
        "arg2": "value2",
    }

    # A download is invoked
    mock_tools.download.file.assert_called_with(
        url="https://example.com/path/to/linuxdeploy-dummy-wonky.AppImage",
        download_path=tmp_path / "tools" / "somewhere",
        role="Dummy plugin",
    )
    # The downloaded file will be made executable
    mock_tools.os.chmod.assert_called_with(appimage_path, 0o755)

    # The build command retains the path to the downloaded file.
    assert linuxdeploy.file_path == appimage_path.parent


def test_verify_does_not_exist_non_appimage(mock_tools, tmp_path):
    """If a non-Appimage tool/plugin doesn't exist, it is downloaded, but not
    elf-patched."""
    tool_path = tmp_path / "tools" / "somewhere" / "linuxdeploy-dummy.sh"

    # Mock a successful download
    mock_tools.download.file.side_effect = side_effect_create_mock_tool(tool_path)

    # Create a linuxdeploy wrapper by verification
    linuxdeploy = LinuxDeployDummy.verify(mock_tools, file_name=tool_path.name)

    # A download is invoked
    mock_tools.download.file.assert_called_with(
        url="https://example.com/path/to/linuxdeploy-dummy.sh",
        download_path=tmp_path / "tools" / "somewhere",
        role="Dummy plugin",
    )
    # The downloaded file will be made executable
    mock_tools.os.chmod.assert_called_with(tool_path, 0o755)

    # The tool content hasn't been altered
    with tool_path.open("r") as f:
        assert f.read() == "I am a complete tool"

    # The build command retains the path to the downloaded file.
    assert linuxdeploy.file_path == tool_path.parent


def test_verify_linuxdeploy_download_failure(mock_tools, tmp_path):
    """If a tool/plugin doesn't exist, and a download failure occurs, an error
    is raised."""
    mock_tools.download.file.side_effect = NetworkFailure("mock")

    with pytest.raises(NetworkFailure, match="Unable to mock"):
        LinuxDeployDummy.verify(mock_tools)

    # A download was invoked
    mock_tools.download.file.assert_called_with(
        url="https://example.com/path/to/linuxdeploy-dummy-wonky.AppImage",
        download_path=tmp_path / "tools" / "somewhere",
        role="Dummy plugin",
    )
