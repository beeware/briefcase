import subprocess

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import confirm_xcode_license_accepted


def test_license_accepted(capsys, mock_tools):
    """If the Xcode license has been accepted, pass without comment."""
    # Check passes without an error...
    confirm_xcode_license_accepted(mock_tools)

    # ... clang was invoked ...
    mock_tools.subprocess.check_output.assert_called_once_with(
        ["/usr/bin/clang", "--version"],
        stderr=subprocess.STDOUT,
    )

    # ... and the user is none the wiser
    out = capsys.readouterr().out
    assert len(out) == 0


def test_unknown_error(capsys, mock_tools):
    """If an unexpected problem occurred accepting the license, warn the
    user."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["/usr/bin/clang", "--version"], returncode=1
    )

    # Check passes without an error...
    confirm_xcode_license_accepted(mock_tools)

    # ... clang was invoked ...
    mock_tools.subprocess.check_output.assert_called_once_with(
        ["/usr/bin/clang", "--version"],
        stderr=subprocess.STDOUT,
    )

    # ...but stdout contains a warning
    out = capsys.readouterr().out
    assert "************" in out


def test_accept_license(mock_tools):
    """If the user accepts the license, continue without error."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["/usr/bin/clang", "--version"], returncode=69
    )

    # Check passes without an error...
    confirm_xcode_license_accepted(mock_tools)

    # ... clang *and* xcodebuild were invoked ...
    mock_tools.subprocess.check_output.assert_called_once_with(
        ["/usr/bin/clang", "--version"],
        stderr=subprocess.STDOUT,
    )
    mock_tools.subprocess.run.assert_called_once_with(
        ["sudo", "xcodebuild", "-license"],
        check=True,
    )


def test_sudo_fail(mock_tools):
    """If the sudo call fails, an exception is raised."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["/usr/bin/clang", "--version"], returncode=69
    )
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=["sudo", "xcodebuild", "-license"], returncode=1
    )

    # Check raises an error:
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase was unable to run the Xcode licensing tool.",
    ):
        confirm_xcode_license_accepted(mock_tools)

    # ... clang *and* xcodebuild were invoked ...
    mock_tools.subprocess.check_output.assert_called_once_with(
        ["/usr/bin/clang", "--version"],
        stderr=subprocess.STDOUT,
    )
    mock_tools.subprocess.run.assert_called_once_with(
        ["sudo", "xcodebuild", "-license"],
        check=True,
    )


def test_license_not_accepted(mock_tools):
    """If the sudo call fails, an exception is raised."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["/usr/bin/clang", "--version"], returncode=69
    )
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=["sudo", "xcodebuild", "-license"], returncode=69
    )

    # Check raises an error:
    with pytest.raises(
        BriefcaseCommandError, match=r"Xcode license has not been accepted."
    ):
        confirm_xcode_license_accepted(mock_tools)

    # ... clang *and* xcodebuild were invoked ...
    mock_tools.subprocess.check_output.assert_called_once_with(
        ["/usr/bin/clang", "--version"],
        stderr=subprocess.STDOUT,
    )
    mock_tools.subprocess.run.assert_called_once_with(
        ["sudo", "xcodebuild", "-license"],
        check=True,
    )


def test_license_status_unknown(capsys, mock_tools):
    """If we get an unusual response from the license, warn but continue."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["/usr/bin/clang", "--version"], returncode=69
    )
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=["sudo", "xcodebuild", "-license"], returncode=42
    )

    # Check passes without error...
    confirm_xcode_license_accepted(mock_tools)

    # ... clang *and* xcodebuild were invoked ...
    mock_tools.subprocess.check_output.assert_called_once_with(
        ["/usr/bin/clang", "--version"],
        stderr=subprocess.STDOUT,
    )
    mock_tools.subprocess.run.assert_called_once_with(
        ["sudo", "xcodebuild", "-license"],
        check=True,
    )

    # ...but stdout contains a warning
    out = capsys.readouterr().out
    assert "************" in out
