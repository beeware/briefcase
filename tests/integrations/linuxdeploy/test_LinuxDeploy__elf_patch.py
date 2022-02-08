from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import MissingToolError
from briefcase.integrations.linuxdeploy import LinuxDeploy
from random import randrange

PATCH = {
        'offset': 0x08,
        'original': bytes.fromhex('414902'),
        'patch': bytes.fromhex('000000')
    }


@pytest.fixture
def mock_command(tmp_path):
    command = MagicMock()
    command.host_arch = 'wonky'
    command.tools_path = tmp_path / 'tools'
    command.tools_path.mkdir()

    return command


def test_patch_linuxdeploy_elf_header_unpatched(mock_command, tmp_path):
    "If linuxdeploy is not patched, patch it."
    appimage_path = tmp_path / 'tools' / 'linuxdeploy-wonky.AppImage'

    # Mock an unpatched linuxdeploy AppImage
    appimage_path.touch()
    with open(appimage_path, 'r+b') as mock_appimage:
        unpatched_header = bytes.fromhex('7f454c46020101004149020000000000')
        mock_appimage.write(unpatched_header)
        mock_appimage.seek(PATCH['offset'])
        pre_patch_header = mock_appimage.read(len(PATCH['original']))

    # Create a linuxdeploy wrapper, then patch the elf header
    linuxdeploy = LinuxDeploy(mock_command)
    linuxdeploy.elf_header_patch()

    # Ensure the patch was applied.
    with open(appimage_path, 'rb') as mock_appimage:
        mock_appimage.seek(PATCH['offset'])
        patched_header = mock_appimage.read(len(PATCH['patch']))

    assert pre_patch_header == PATCH['original']
    assert patched_header == PATCH['patch']


def test_patch_linuxdeploy_elf_header_already_patched(mock_command, tmp_path):
    "If linuxdeploy is already patched, don't patch it."
    appimage_path = tmp_path / 'tools' / 'linuxdeploy-wonky.AppImage'

    # Mock a patched linuxdeploy AppImage
    appimage_path.touch()
    with open(appimage_path, 'r+b') as mock_appimage:
        patched_header = bytes.fromhex('7f454c46020101000000000000000000')
        mock_appimage.write(patched_header)
        mock_appimage.seek(PATCH['offset'])
        pre_patch_header = mock_appimage.read(len(PATCH['original']))

    # Create a linuxdeploy wrapper, then patch the elf header
    linuxdeploy = LinuxDeploy(mock_command)
    linuxdeploy.elf_header_patch()

    # Ensure the patch was applied.
    with open(appimage_path, 'rb') as mock_appimage:
        mock_appimage.seek(PATCH['offset'])
        patched_header = mock_appimage.read(len(PATCH['patch']))

    assert pre_patch_header == PATCH['patch']
    assert patched_header == PATCH['patch']


def test_patch_linuxdeploy_elf_header_bad_appimage(mock_command, tmp_path):
    "If linuxdeploy does not have a valid header, raise an error."
    appimage_path = tmp_path / 'tools' / 'linuxdeploy-wonky.AppImage'

    # Mock an bad linuxdeploy AppImage
    appimage_path.touch()
    with open(appimage_path, 'r+b') as mock_appimage:
        unpatched_header = bytes.fromhex('%030x' % randrange(16**30))
        mock_appimage.write(unpatched_header)

    # Create a linuxdeploy wrapper, then patch the elf header
    linuxdeploy = LinuxDeploy(mock_command)
    with pytest.raises(MissingToolError):
        linuxdeploy = linuxdeploy.elf_header_patch()
