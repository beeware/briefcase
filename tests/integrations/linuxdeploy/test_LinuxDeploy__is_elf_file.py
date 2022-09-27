import pytest

from briefcase.integrations.linuxdeploy import LinuxDeployBase
from tests.integrations.linuxdeploy.utils import create_mock_appimage


@pytest.fixture
def linuxdeploy(mock_tools, tmp_path):
    class LinuxDeployDummy(LinuxDeployBase):
        name = "dummy-plugin"

        @property
        def file_name(self):
            return "linuxdeploy-dummy-wonky.AppImage"

        @property
        def download_url(self):
            return "https://example.com/path/to/linuxdeploy-dummy-wonky.AppImage"

        @property
        def file_path(self):
            return tmp_path / "plugin"

    return LinuxDeployDummy(mock_tools)


def test_is_elf_header_positive_detection(linuxdeploy, tmp_path):
    """File with an ELF Header is identified as an ELF file."""
    create_mock_appimage(
        appimage_path=tmp_path / "plugin" / "linuxdeploy-dummy-wonky.AppImage"
    )
    assert linuxdeploy.is_elf_file() is True


def test_is_elf_header_negative_detection(linuxdeploy, tmp_path):
    """File without an ELF Header is not identified as an ELF file."""
    create_mock_appimage(
        appimage_path=tmp_path / "plugin" / "linuxdeploy-dummy-wonky.AppImage",
        mock_appimage_kind="corrupt",
    )
    assert linuxdeploy.is_elf_file() is False


def test_is_elf_header_empty_file(linuxdeploy, tmp_path):
    """Empty file is not identified as an ELF file without any errors."""
    create_mock_appimage(
        appimage_path=tmp_path / "plugin" / "linuxdeploy-dummy-wonky.AppImage",
        mock_appimage_kind="empty",
    )
    assert linuxdeploy.is_elf_file() is False
