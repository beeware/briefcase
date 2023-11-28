from tests.integrations.linuxdeploy.utils import create_mock_appimage


def test_is_elf_header_positive_detection(linuxdeploy, tmp_path):
    """File with an ELF Header is identified as an ELF file."""
    create_mock_appimage(appimage_path=tmp_path / "tools/linuxdeploy-i386.AppImage")
    assert linuxdeploy.is_elf_file() is True


def test_is_elf_header_negative_detection(linuxdeploy, tmp_path):
    """File without an ELF Header is not identified as an ELF file."""
    create_mock_appimage(
        appimage_path=tmp_path / "tools/linuxdeploy-i386.AppImage",
        mock_appimage_kind="corrupt",
    )
    assert linuxdeploy.is_elf_file() is False


def test_is_elf_header_empty_file(linuxdeploy, tmp_path):
    """Empty file is not identified as an ELF file without any errors."""
    create_mock_appimage(
        appimage_path=tmp_path / "tools/linuxdeploy-i386.AppImage",
        mock_appimage_kind="empty",
    )
    assert linuxdeploy.is_elf_file() is False
