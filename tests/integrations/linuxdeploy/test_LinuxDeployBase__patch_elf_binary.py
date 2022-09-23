import pytest

from briefcase.exceptions import CorruptToolError
from briefcase.integrations.linuxdeploy import (
    ELF_PATCH_OFFSET,
    ELF_PATCH_ORIGINAL_BYTES,
    ELF_PATCH_PATCHED_BYTES,
    LinuxDeployBase,
)
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


def test_patch_linuxdeploy_elf_header_unpatched(linuxdeploy, tmp_path):
    """If the linuxdeploy tool/plugin is not patched, patch it."""
    appimage_path = tmp_path / "plugin" / "linuxdeploy-dummy-wonky.AppImage"

    # Mock an unpatched linuxdeploy AppImage
    pre_patch_header = create_mock_appimage(
        appimage_path=appimage_path, mock_appimage_kind="original"
    )

    # Create a linuxdeploy wrapper, then patch the elf header
    linuxdeploy.patch_elf_header()

    # Ensure the patch was applied.
    with open(appimage_path, "rb") as mock_appimage:
        mock_appimage.seek(ELF_PATCH_OFFSET)
        patched_header = mock_appimage.read(len(ELF_PATCH_PATCHED_BYTES))

    assert pre_patch_header == ELF_PATCH_ORIGINAL_BYTES
    assert patched_header == ELF_PATCH_PATCHED_BYTES


def test_patch_linuxdeploy_elf_header_already_patched(linuxdeploy, tmp_path):
    """If linuxdeploy is already patched, don't patch it."""
    appimage_path = tmp_path / "plugin" / "linuxdeploy-dummy-wonky.AppImage"

    # Mock a patched linuxdeploy AppImage
    pre_patch_header = create_mock_appimage(
        appimage_path=appimage_path, mock_appimage_kind="patched"
    )

    # Create a linuxdeploy wrapper, then patch the elf header
    linuxdeploy.patch_elf_header()

    # Ensure the patch was applied.
    with open(appimage_path, "rb") as mock_appimage:
        mock_appimage.seek(ELF_PATCH_OFFSET)
        patched_header = mock_appimage.read(len(ELF_PATCH_PATCHED_BYTES))

    assert pre_patch_header == ELF_PATCH_PATCHED_BYTES
    assert patched_header == ELF_PATCH_PATCHED_BYTES


def test_patch_linuxdeploy_elf_header_bad_appimage(linuxdeploy, tmp_path):
    """If linuxdeploy does not have a valid header, raise an error."""
    appimage_path = tmp_path / "plugin" / "linuxdeploy-dummy-wonky.AppImage"

    # Mock a bad linuxdeploy AppImage
    create_mock_appimage(appimage_path=appimage_path, mock_appimage_kind="corrupt")

    # Create a linuxdeploy wrapper, then patch the elf header
    with pytest.raises(CorruptToolError):
        linuxdeploy = linuxdeploy.patch_elf_header()


def test_patch_linuxdeploy_elf_header_empty_appimage(linuxdeploy, tmp_path):
    """If file is empty, raise an error."""
    appimage_path = tmp_path / "plugin" / "linuxdeploy-dummy-wonky.AppImage"

    # Mock a bad linuxdeploy AppImage
    create_mock_appimage(appimage_path=appimage_path, mock_appimage_kind="empty")

    # Create a linuxdeploy wrapper, then patch the elf header
    with pytest.raises(CorruptToolError):
        linuxdeploy = linuxdeploy.patch_elf_header()
