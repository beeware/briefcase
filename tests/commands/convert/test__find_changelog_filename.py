import pytest

from briefcase.platforms.linux.system import find_changelog_filename

from ...utils import create_file


def test_no_changelog(tmp_path):
    """Changelog file does not exist"""
    assert find_changelog_filename(tmp_path) is None


def test_no_valid_changelog(tmp_path):
    """Changelog file exists but with invalid name format so its not accepted"""
    changelog_file = tmp_path / "base_path/invalid_changelog_format"
    create_file(changelog_file, "First App Changelog")
    assert find_changelog_filename(tmp_path / "base_path") is None


@pytest.mark.parametrize(
    "changelog_filename",
    [
        f"{name}{extension}"
        for name in ["CHANGELOG", "HISTORY", "NEWS", "RELEASES"]
        for extension in ["", ".md", ".rst", ".txt"]
    ],
)
def test_has_changelog(tmp_path, changelog_filename):
    """Makes sure all formats are accepted"""
    changelog_file = tmp_path / f"base_path/{changelog_filename}"
    create_file(changelog_file, "First App Changelog")
    assert find_changelog_filename(tmp_path / "base_path") == changelog_filename


def test_multiple_changefile(tmp_path):
    """If there's more than one changelog, only one is found."""

    changelog_file1 = tmp_path / "base_path/NEWS.txt"
    changelog_file2 = tmp_path / "base_path/CHANGELOG.md"
    create_file(changelog_file1, "First App Changelog")
    create_file(changelog_file2, "First App Changelog")
    assert find_changelog_filename(tmp_path / "base_path") == "CHANGELOG.md"
