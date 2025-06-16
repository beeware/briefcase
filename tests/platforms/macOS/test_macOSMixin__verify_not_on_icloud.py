import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_on_icloud(dummy_command, first_app_templated, tmp_path):
    """If the path is on iCloud, the metadata is detected."""
    dummy_command.tools.subprocess.check_output.return_value = (
        "com.apple.fileprovider.fpfs#P: \n"
    )

    # Verify the location
    with pytest.raises(
        BriefcaseCommandError,
        match=r"app folder, move your project to location\nthat is not",
    ):
        dummy_command.verify_not_on_icloud(first_app_templated)

    # The subprocess call was what we expect
    dummy_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "xattr",
            "-p",
            "com.apple.fileprovider.fpfs#P",
            tmp_path / "base_path/build/first-app/macos/app/First App.app",
        ],
        quiet=1,
    )

    # The bundle hasn't been cleaned up
    assert (tmp_path / "base_path/build/first-app/macos/app").exists()


def test_on_icloud_with_cleanup(dummy_command, first_app_templated, tmp_path):
    """If the path is on iCloud, the metadata is detected, and the bundle can be cleaned up."""
    dummy_command.tools.subprocess.check_output.return_value = (
        "com.apple.fileprovider.fpfs#P: \n"
    )

    # Verify the location
    with pytest.raises(
        BriefcaseCommandError,
        match=r"\n\nMove your project to a location that is not synchronized",
    ):
        dummy_command.verify_not_on_icloud(first_app_templated, cleanup=True)

    # The subprocess call was what we expect
    dummy_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "xattr",
            "-p",
            "com.apple.fileprovider.fpfs#P",
            tmp_path / "base_path/build/first-app/macos/app/First App.app",
        ],
        quiet=1,
    )

    # The bundle has been cleaned up
    assert not (tmp_path / "base_path/build/first-app/macos/app").exists()


def test_not_on_icloud(dummy_command, first_app_templated, tmp_path):
    """If the path *not* is on iCloud, the metadata is detected."""
    dummy_command.tools.subprocess.check_output.side_effect = (
        subprocess.CalledProcessError(returncode=1, cmd="xattr")
    )

    # The location can be verified
    dummy_command.verify_not_on_icloud(first_app_templated)

    # The subprocess call was what we expect
    dummy_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "xattr",
            "-p",
            "com.apple.fileprovider.fpfs#P",
            tmp_path / "base_path/build/first-app/macos/app/First App.app",
        ],
        quiet=1,
    )

    # The bundle still exists
    assert (tmp_path / "base_path/build/first-app/macos/app").exists()


def test_app_doesnt_exist(dummy_command, first_app, tmp_path):
    """If the path hasn't been generated yet, verification succeeds."""
    dummy_command.tools.subprocess.check_output.side_effect = (
        subprocess.CalledProcessError(returncode=1, cmd="xattr")
    )

    # The location can be verified
    dummy_command.verify_not_on_icloud(first_app)

    # The subprocess call was what we expect
    dummy_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "xattr",
            "-p",
            "com.apple.fileprovider.fpfs#P",
            tmp_path / "base_path/build/first-app/macos/app/First App.app",
        ],
        quiet=1,
    )

    # The bundle doesn't exist
    assert not (tmp_path / "base_path/build/first-app/macos/app").exists()
