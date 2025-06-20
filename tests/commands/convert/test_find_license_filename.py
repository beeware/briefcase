import pytest

from briefcase.platforms.linux.system import find_license_filename

from ...utils import create_file


def test_no_license(tmp_path):
    """License file does not exist"""
    assert find_license_filename(tmp_path) is None


def test_no_valid_license(tmp_path):
    """License file exists but with invalid name format so its not accepted"""
    license_file = tmp_path / "base_path/invalid_license_format"
    create_file(license_file, "First App License")
    assert find_license_filename(tmp_path / "base_path") is None


@pytest.mark.parametrize(
    "license_filename",
    [
        f"{name}{extension}"
        for name in ["LICENSE", "LICENCE", "COPYING"]
        for extension in ["", ".md", ".rst", ".txt"]
    ],
)
def test_has_license(tmp_path, license_filename):
    """Makes sure all formats are accepted"""
    license_file = tmp_path / f"base_path/{license_filename}"
    create_file(license_file, "First App License")
    assert find_license_filename(tmp_path / "base_path") == license_filename


def test_multiple_changefile(tmp_path):
    """If there's more than one license, only one is found."""

    license_file1 = tmp_path / "base_path/LICENCE.txt"
    license_file2 = tmp_path / "base_path/LICENSE.md"
    create_file(license_file1, "First App License")
    create_file(license_file2, "First App Licence")
    assert find_license_filename(tmp_path / "base_path") == "LICENSE.md"
