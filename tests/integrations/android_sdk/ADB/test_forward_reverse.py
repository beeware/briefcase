import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_forward(mock_tools, adb):
    """An port forwarding."""
    # Invoke forward
    adb.forward(5555, 6666)

    # Validate call parameters.
    mock_tools.subprocess.check_output.assert_called_once_with(
        [
            mock_tools.android_sdk.adb_path,
            "-s",
            "exampleDevice",
            "forward",
            "tcp:5555",
            "tcp:6666",
        ],
    )


def test_forward_failure(adb, mock_tools):
    """If port forwarding fails, the error is caught."""
    # Mock out the run command on an adb instance
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=""
    )
    with pytest.raises(BriefcaseCommandError):
        adb.forward(5555, 6666)


def test_forward_remove(mock_tools, adb):
    """An port forwarding removing."""
    # Invoke forward remove
    adb.forward_remove(5555)

    # Validate call parameters.
    mock_tools.subprocess.check_output.assert_called_once_with(
        [
            mock_tools.android_sdk.adb_path,
            "-s",
            "exampleDevice",
            "forward",
            "--remove",
            "tcp:5555",
        ],
    )


def test_forward_remove_failure(adb, mock_tools):
    """If port forwarding removing fails, the error is caught."""
    # Mock out the run command on an adb instance
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=""
    )
    with pytest.raises(BriefcaseCommandError):
        adb.forward_remove(5555)


def test_reverse(mock_tools, adb):
    """An port reversing."""
    # Invoke reverse
    adb.reverse(5555, 6666)

    # Validate call parameters.
    mock_tools.subprocess.check_output.assert_called_once_with(
        [
            mock_tools.android_sdk.adb_path,
            "-s",
            "exampleDevice",
            "reverse",
            "tcp:5555",
            "tcp:6666",
        ],
    )


def test_reverse_failure(adb, mock_tools):
    """If port reversing fails, the error is caught."""
    # Mock out the run command on an adb instance
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=""
    )
    with pytest.raises(BriefcaseCommandError):
        adb.reverse(5555, 6666)


def test_reverse_remove(mock_tools, adb):
    """An port reversing removing."""
    # Invoke reverse remove
    adb.reverse_remove(5555)

    # Validate call parameters.
    mock_tools.subprocess.check_output.assert_called_once_with(
        [
            mock_tools.android_sdk.adb_path,
            "-s",
            "exampleDevice",
            "reverse",
            "--remove",
            "tcp:5555",
        ],
    )


def test_reverse_remove_failure(adb, mock_tools):
    """If port reversing removing fails, the error is caught."""
    # Mock out the run command on an adb instance
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=""
    )
    with pytest.raises(BriefcaseCommandError):
        adb.reverse_remove(5555)
