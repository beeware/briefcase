from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import CorruptToolError, MissingToolError
from briefcase.integrations.linuxdeploy import (
    ELF_PATCH_OFFSET,
    ELF_PATCH_ORIGINAL_BYTES,
    ELF_PATCH_PATCHED_BYTES,
    LinuxDeploy,
)
from tests.integrations.linuxdeploy.utils import create_mock_appimage


@pytest.fixture
def mock_command(tmp_path):
    command = MagicMock()
    command.host_arch = "wonky"
    command.tools_path = tmp_path / "tools"
    command.tools_path.mkdir()

    return command


def test_patch_linuxdeploy_elf_header_unpatched(mock_command, tmp_path):
    """If linuxdeploy is not patched, patch it."""
    appimage_path = tmp_path / "tools" / "linuxdeploy-wonky.AppImage"

    # Mock an unpatched linuxdeploy AppImage
    pre_patch_header = create_mock_appimage(
        appimage_path=appimage_path, mock_appimage_kind="original"
    )

    # Create a linuxdeploy wrapper, then patch the elf header
    linuxdeploy = LinuxDeploy(mock_command)
    linuxdeploy.patch_elf_header()

    # Ensure the patch was applied.
    with open(appimage_path, "rb") as mock_appimage:
        mock_appimage.seek(ELF_PATCH_OFFSET)
        patched_header = mock_appimage.read(len(ELF_PATCH_PATCHED_BYTES))

    assert pre_patch_header == ELF_PATCH_ORIGINAL_BYTES
    assert patched_header == ELF_PATCH_PATCHED_BYTES


def test_patch_linuxdeploy_elf_header_already_patched(mock_command, tmp_path):
    """If linuxdeploy is already patched, don't patch it."""
    appimage_path = tmp_path / "tools" / "linuxdeploy-wonky.AppImage"

    # Mock a patched linuxdeploy AppImage
    pre_patch_header = create_mock_appimage(
        appimage_path=appimage_path, mock_appimage_kind="patched"
    )

    # Create a linuxdeploy wrapper, then patch the elf header
    linuxdeploy = LinuxDeploy(mock_command)
    linuxdeploy.patch_elf_header()

    # Ensure the patch was applied.
    with open(appimage_path, "rb") as mock_appimage:
        mock_appimage.seek(ELF_PATCH_OFFSET)
        patched_header = mock_appimage.read(len(ELF_PATCH_PATCHED_BYTES))

    assert pre_patch_header == ELF_PATCH_PATCHED_BYTES
    assert patched_header == ELF_PATCH_PATCHED_BYTES


def test_patch_linuxdeploy_elf_header_bad_appimage(mock_command, tmp_path):
    """If linuxdeploy does not have a valid header, raise an error."""
    appimage_path = tmp_path / "tools" / "linuxdeploy-wonky.AppImage"

    # Mock an bad linuxdeploy AppImage
    create_mock_appimage(appimage_path=appimage_path, mock_appimage_kind="corrupt")

    # Create a linuxdeploy wrapper, then patch the elf header
    linuxdeploy = LinuxDeploy(mock_command)
    with pytest.raises(CorruptToolError):
        linuxdeploy = linuxdeploy.patch_elf_header()


def test_patch_linuxdeploy_elf_header_no_file(mock_command, tmp_path):
    """If there is no linuxdeploy AppImage, raise an error."""
    # Create a linuxdeploy wrapper, then patch the elf header
    linuxdeploy = LinuxDeploy(mock_command)
    with pytest.raises(MissingToolError):
        linuxdeploy = linuxdeploy.patch_elf_header()
