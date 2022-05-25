import os
import subprocess
from unittest import mock

import pytest

from briefcase.console import Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import ensure_xcode_is_installed


@pytest.fixture
def xcode(tmp_path):
    """Create a dummy location for Xcode."""
    xcode_location = tmp_path / "Xcode.app"
    xcode_location.mkdir(parents=True, exist_ok=True)
    return os.fsdecode(xcode_location)


def test_not_installed(tmp_path):
    """If Xcode is not installed, raise an error."""
    command = mock.MagicMock()
    command.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["xcode-select", "-p"], returncode=2
    )

    # Test a location where Xcode *won't* be installed
    with pytest.raises(BriefcaseCommandError):
        ensure_xcode_is_installed(command)


def test_not_installed_hardcoded_path(tmp_path):
    """If Xcode is not installed at the given location, raise an error."""
    command = mock.MagicMock()
    command.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["xcodebuild", "-version"], returncode=1
    )

    # Test a location where Xcode *won't* be installed
    with pytest.raises(BriefcaseCommandError):
        ensure_xcode_is_installed(
            command,
            xcode_location=tmp_path / "Xcode.app",
        )

    # xcode-select was not invoked
    command.subprocess.check_output.assert_not_called()


def test_exists_but_command_line_tools_selected(xcode):
    """If the Xcode folder exists, but cmd-line tools are selected, raise an
    error."""
    command = mock.MagicMock()
    command.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["xcodebuild", "-version"], returncode=1
    )
    command.subprocess.check_output.side_effect.output = (
        "xcode-select: error: tool 'xcodebuild' requires Xcode, but "
        "active developer directory '/Library/Developer/CommandLineTools' "
        "is a command line tools instance\n"
    )

    with pytest.raises(BriefcaseCommandError, match=r"xcode-select --switch"):
        ensure_xcode_is_installed(command, xcode_location=xcode)

    # xcode-select was invoked
    command.subprocess.check_output.assert_called_once_with(
        ["xcodebuild", "-version"],
        stderr=subprocess.STDOUT,
    )


def test_exists_but_corrupted(xcode):
    """If the Xcode folder exists, but xcodebuild breaks, raise an error."""
    command = mock.MagicMock()
    command.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["xcodebuild", "-version"], returncode=1
    )
    command.subprocess.check_output.side_effect.output = "Badness occurred."

    with pytest.raises(
        BriefcaseCommandError, match=r"should return the current Xcode version"
    ):
        ensure_xcode_is_installed(command, xcode_location=xcode)

    # xcode-select was invoked
    command.subprocess.check_output.assert_called_once_with(
        ["xcodebuild", "-version"],
        stderr=subprocess.STDOUT,
    )


def test_installed_no_minimum_version(xcode):
    """If Xcode is installed, but there's no minimum version, check is
    satisfied."""
    command = mock.MagicMock()
    command.subprocess.check_output.return_value = (
        "Xcode 11.2.1\nBuild version 11B500\n"
    )

    # Check passes without an error.
    ensure_xcode_is_installed(command, xcode_location=xcode)

    # xcode-select was invoked
    command.subprocess.check_output.assert_called_once_with(
        ["xcodebuild", "-version"],
        stderr=subprocess.STDOUT,
    )


def test_installed_extra_output(capsys, xcode):
    """If Xcode but outputs extra content, the check is still satisfied."""
    # This specific output was seen in the wild with Xcode 13.2.1; see #668
    command = mock.MagicMock()
    command.logger = Log()
    command.subprocess.check_output.return_value = "\n".join(
        [
            "objc[86306]: Class AMSupportURLConnectionDelegate is implemented in both /usr/lib/libauthinstall.dylib (0x20d17ab90) and /Library/Apple/System/Library/PrivateFrameworks/MobileDevice.framework/Versions/A/MobileDevice (0x1084b82c8). One of the two will be used. Which one is undefined."  # noqa: E501
            "objc[86306]: Class AMSupportURLSession is implemented in both /usr/lib/libauthinstall.dylib (0x20d17abe0) and /Library/Apple/System/Library/PrivateFrameworks/MobileDevice.framework/Versions/A/MobileDevice (0x1084b8318). One of the two will be used. Which one is undefined.",  # noqa: E501
            "Xcode 13.2.1",
            "Build version 13C100",
        ]
    )

    # Check passes without an error.
    ensure_xcode_is_installed(command, xcode_location=xcode, min_version=(11, 1))

    # xcode-select was invoked
    command.subprocess.check_output.assert_called_once_with(
        ["xcodebuild", "-version"],
        stderr=subprocess.STDOUT,
    )

    # No warning generated.
    out = capsys.readouterr().out
    assert "WARNING" not in out


@pytest.mark.parametrize(
    "min_version, version",
    [
        # Exact match
        ((11, 2, 1), "11.2.1"),  # Exact match
        ((11, 2), "11.2.0"),  # Exact match, implied revision.
        ((11,), "11.0.0"),  # Exact match, implied minor version.
        # Rules still work for single digit versions
        ((8, 2, 1), "8.2.1"),  # Exact match
        ((8, 2), "8.2.0"),  # Exact match, implied revision.
        ((8,), "8.0.0"),  # Exact match, implied minor version.
        # Exceeds version
        ((11, 2, 1), "11.2.5"),  # Exceeds revision requirement
        ((11, 2, 1), "11.3.0"),  # Exceeds minor requirement
        ((11, 2, 1), "12.0.0"),  # Exceeds major requirement
        ((11, 2), "11.2.5"),  # Exceeds implied revision requirement
        ((11, 2), "11.3.0"),  # Exceeds minor requirement
        ((11, 2), "12.0.0"),  # Exceeds major requirement
        ((11,), "11.2.5"),  # Exceeds implied revision requirement
        ((11,), "11.3.0"),  # Exceeds implied minor requirement
        ((11,), "12.0.0"),  # Exceeds major requirement
        # 2 digit version number
        # exact match
        ((11, 2, 0), "11.2"),  # Exact match.
        ((11, 2), "11.2"),  # Exact match, implied revision.
        ((11,), "11.2"),  # Exact match, implied minor version.
        # exceeds version
        ((11, 1, 1), "11.2"),  # Exact match.
        ((11, 1), "11.2"),  # Exact match, implied revision.
        ((11,), "11.2"),  # Exact match, implied minor version.
    ],
)
def test_installed_with_minimum_version_success(min_version, version, capsys, xcode):
    """Check XCode can meet a minimum version requirement."""

    def check_output_mock(cmd_list, *args, **kwargs):

        if cmd_list == ["xcode-select", "-p"]:
            return xcode + "\n"

        if cmd_list == ["xcodebuild", "-version"]:
            return f"Xcode {version}\nBuild version 11B500\n"

        return mock.DEFAULT

    command = mock.MagicMock()
    command.subprocess.check_output.side_effect = check_output_mock

    # Check passes without an error.
    ensure_xcode_is_installed(
        command,
        min_version=min_version,
    )

    # assert xcode-select and xcodebuild were invoked
    command.subprocess.check_output.assert_has_calls(
        [
            mock.call(
                ["xcode-select", "-p"],
                stderr=subprocess.STDOUT,
            ),
            mock.call(
                ["xcodebuild", "-version"],
                stderr=subprocess.STDOUT,
            ),
        ],
        any_order=False,
    )

    # Make sure the warning wasn't displayed.
    out = capsys.readouterr().out
    assert "WARNING" not in out


@pytest.mark.parametrize(
    "min_version, version",
    [
        ((11, 2, 5), "11.2.1"),  # insufficient revision
        ((11, 3), "11.2.1"),  # Insufficient micro version
        ((12,), "11.2.1"),  # Insufficient major version
        ((8, 2, 5), "8.2.1"),  # insufficient revision
        ((8, 3), "8.2.1"),  # Insufficient micro version
        ((9,), "8.2.1"),  # Insufficient major version
    ],
)
def test_installed_with_minimum_version_failure(min_version, version, xcode):
    """Check XCode fail to meet a minimum version requirement."""
    command = mock.MagicMock()
    command.subprocess.check_output.return_value = (
        f"Xcode {version}\nBuild version 11B500\n"
    )

    # Check raises an error.
    with pytest.raises(BriefcaseCommandError):
        ensure_xcode_is_installed(
            command,
            min_version=min_version,
            xcode_location=xcode,
        )

    # xcode-select was invoked
    command.subprocess.check_output.assert_called_once_with(
        ["xcodebuild", "-version"],
        stderr=subprocess.STDOUT,
    )


def test_unexpected_version_output(capsys, xcode):
    """If xcodebuild returns unexpected output, assume it's ok..."""
    command = mock.MagicMock()
    command.logger = Log()
    command.subprocess.check_output.return_value = "Wibble Wibble Wibble\n"

    # Check passes without an error...
    ensure_xcode_is_installed(
        command,
        min_version=(11, 2, 1),
        xcode_location=xcode,
    )

    # xcode-select was invoked
    command.subprocess.check_output.assert_called_once_with(
        ["xcodebuild", "-version"],
        stderr=subprocess.STDOUT,
    )

    # ...but stdout contains a warning
    out = capsys.readouterr().out
    assert "************" in out
