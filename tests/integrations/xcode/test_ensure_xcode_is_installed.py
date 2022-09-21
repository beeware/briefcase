import os
import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import ensure_xcode_is_installed


@pytest.fixture
def default_xcode_install_path(tmp_path):
    return tmp_path / "Applications" / "Xcode.app"


@pytest.fixture
def xcode(default_xcode_install_path):
    """Create a dummy location for Xcode."""
    default_xcode_install_path.mkdir(parents=True, exist_ok=True)
    return os.fsdecode(default_xcode_install_path)


def test_not_installed(tmp_path, mock_tools):
    """If No Xcode is installed, raise an error."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["xcode-select", "-p"], returncode=2
    )

    # Test a location where Xcode *won't* be installed
    with pytest.raises(BriefcaseCommandError):
        ensure_xcode_is_installed(mock_tools)

    # subprocess was invoked as expected
    mock_tools.subprocess.check_output.assert_has_calls(
        [
            mock.call(
                ["xcode-select", "-p"],
                stderr=subprocess.STDOUT,
            ),
        ],
        any_order=False,
    )


def test_custom_install_location(default_xcode_install_path, tmp_path, mock_tools):
    """If Xcode is in a non-default location, that's fine."""
    # Create a custom Xcode location
    custom_xcode_location = tmp_path / "custom" / "Xcode.app"
    custom_xcode_location.mkdir(parents=True, exist_ok=True)

    mock_tools.subprocess.check_output.side_effect = [
        os.fsdecode(custom_xcode_location) + "\n",  # xcode-select -p
        "Xcode 13.3.1\nBuild version 11B500\n",  # xcodebuild -version
    ]

    ensure_xcode_is_installed(mock_tools, xcode_location=default_xcode_install_path)

    # subprocess was invoked as expected
    mock_tools.subprocess.check_output.assert_has_calls(
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


def test_command_line_tools_only(default_xcode_install_path, mock_tools):
    """If the cmdline tools are installed, but Xcode isn't, raise an error."""
    mock_tools.subprocess.check_output.side_effect = [
        "/Library/Developer/CommandLineTools\n",  # xcode-select -p
        subprocess.CalledProcessError(
            cmd=["xcodebuild", "-version"],
            returncode=1,
            output="xcode-select: error: tool 'xcodebuild' requires Xcode, but "
            "active developer directory '/Library/Developer/CommandLineTools' "
            "is a command line tools instance\n",
        ),
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"You have the Xcode command line tools installed",
    ):
        ensure_xcode_is_installed(mock_tools, xcode_location=default_xcode_install_path)

    # subprocess was invoked as expected
    mock_tools.subprocess.check_output.assert_has_calls(
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


def test_installed_but_command_line_tools_selected(
    default_xcode_install_path,
    xcode,
    mock_tools,
):
    """If Xcode is installed, but the cmdline tools are selected raise an
    error."""
    mock_tools.subprocess.check_output.side_effect = [
        xcode + "\n",  # xcode-select -p
        subprocess.CalledProcessError(
            cmd=["xcodebuild", "-version"],
            returncode=1,
            output="xcode-select: error: tool 'xcodebuild' requires Xcode, but "
            "active developer directory '/Library/Developer/CommandLineTools' "
            "is a command line tools instance\n",
        ),
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Xcode appears to be installed, but the active developer directory ",
    ):
        ensure_xcode_is_installed(mock_tools, xcode_location=default_xcode_install_path)

    # subprocess was invoked as expected
    mock_tools.subprocess.check_output.assert_has_calls(
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


def test_custom_install_with_command_line_tools(
    default_xcode_install_path,
    tmp_path,
    mock_tools,
):
    """If the cmdline tools are installed, and Xcode is in a non-default
    location, raise an error."""
    # Create a custom Xcode location
    custom_xcode_location = tmp_path / "custom" / "Xcode.app"
    custom_xcode_location.mkdir(parents=True, exist_ok=True)

    mock_tools.subprocess.check_output.side_effect = [
        "/Library/Developer/CommandLineTools\n",  # xcode-select -p
        subprocess.CalledProcessError(
            cmd=["xcodebuild", "-version"],
            returncode=1,
            output="xcode-select: error: tool 'xcodebuild' requires Xcode, but "
            "active developer directory '/Library/Developer/CommandLineTools' "
            "is a command line tools instance\n",
        ),
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"You have the Xcode command line tools installed",
    ):
        ensure_xcode_is_installed(mock_tools, xcode_location=default_xcode_install_path)

    # subprocess was invoked as expected
    mock_tools.subprocess.check_output.assert_has_calls(
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


def test_installed_but_corrupted(xcode, mock_tools):
    """If the Xcode folder exists, but xcodebuild breaks, raise an error."""
    mock_tools.subprocess.check_output.side_effect = [
        xcode + "\n",  # xcode-select -p
        subprocess.CalledProcessError(
            cmd=["xcodebuild", "-version"],
            returncode=1,
            output="Badness occurred",
        ),
    ]

    with pytest.raises(
        BriefcaseCommandError, match=r"should return the current Xcode version"
    ):
        ensure_xcode_is_installed(mock_tools, xcode_location=xcode)

    # subprocess was invoked as expected
    mock_tools.subprocess.check_output.assert_has_calls(
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


def test_installed_no_minimum_version(xcode, mock_tools):
    """If Xcode is installed, but there's no minimum version, check is
    satisfied."""
    mock_tools.subprocess.check_output.side_effect = [
        xcode + "\n",  # xcode-select -p
        "Xcode 11.2.1\nBuild version 11B500\n",  # xcodebuild -version
    ]

    # Check passes without an error.
    ensure_xcode_is_installed(mock_tools, xcode_location=xcode)

    # subprocess was invoked as expected
    mock_tools.subprocess.check_output.assert_has_calls(
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


def test_installed_extra_output(capsys, xcode, mock_tools):
    """If Xcode but outputs extra content, the check is still satisfied."""
    # This specific output was seen in the wild with Xcode 13.2.1; see #668
    mock_tools.subprocess.check_output.side_effect = [
        xcode + "\n",  # xcode-select -p
        "\n".join(
            [
                "objc[86306]: Class AMSupportURLConnectionDelegate is implemented in both /usr/lib/libauthinstall.dylib (0x20d17ab90) and /Library/Apple/System/Library/PrivateFrameworks/MobileDevice.framework/Versions/A/MobileDevice (0x1084b82c8). One of the two will be used. Which one is undefined."  # noqa: E501
                "objc[86306]: Class AMSupportURLSession is implemented in both /usr/lib/libauthinstall.dylib (0x20d17abe0) and /Library/Apple/System/Library/PrivateFrameworks/MobileDevice.framework/Versions/A/MobileDevice (0x1084b8318). One of the two will be used. Which one is undefined.",  # noqa: E501
                "Xcode 13.2.1",
                "Build version 13C100",
            ]
        ),
    ]

    # Check passes without an error.
    ensure_xcode_is_installed(mock_tools, xcode_location=xcode, min_version=(11, 1))

    # subprocess was invoked as expected
    mock_tools.subprocess.check_output.assert_has_calls(
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
def test_installed_with_minimum_version_success(
    min_version,
    version,
    capsys,
    xcode,
    mock_tools,
):
    """Check XCode can meet a minimum version requirement."""

    def check_output_mock(cmd_list, *args, **kwargs):
        if cmd_list == ["xcode-select", "-p"]:
            return xcode + "\n"

        if cmd_list == ["xcodebuild", "-version"]:
            return f"Xcode {version}\nBuild version 11B500\n"

        return mock.DEFAULT

    mock_tools.subprocess.check_output.side_effect = check_output_mock

    # Check passes without an error.
    ensure_xcode_is_installed(
        mock_tools,
        min_version=min_version,
    )

    # assert xcode-select and xcodebuild were invoked
    mock_tools.subprocess.check_output.assert_has_calls(
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
def test_installed_with_minimum_version_failure(
    min_version,
    version,
    xcode,
    mock_tools,
):
    """Check XCode fail to meet a minimum version requirement."""
    mock_tools.subprocess.check_output.side_effect = [
        xcode + "\n",  # xcode-select -p
        f"Xcode {version}\nBuild version 11B500\n",  # xcodebuild -version
    ]

    # Check raises an error.
    with pytest.raises(BriefcaseCommandError):
        ensure_xcode_is_installed(
            mock_tools,
            min_version=min_version,
            xcode_location=xcode,
        )

    # subprocess was invoked as expected
    mock_tools.subprocess.check_output.assert_has_calls(
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


def test_unexpected_version_output(capsys, xcode, mock_tools):
    """If xcodebuild returns unexpected output, assume it's ok..."""
    mock_tools.subprocess.check_output.side_effect = [
        xcode + "\n",  # xcode-select -p
        "Wibble Wibble Wibble\n",  # xcodebuild -version
    ]

    # Check passes without an error...
    ensure_xcode_is_installed(
        mock_tools,
        min_version=(11, 2, 1),
        xcode_location=xcode,
    )

    # subprocess was invoked as expected
    mock_tools.subprocess.check_output.assert_has_calls(
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

    # ...but stdout contains a warning
    out = capsys.readouterr().out
    assert "************" in out
