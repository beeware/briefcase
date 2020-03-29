import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import ensure_xcode_is_installed


@pytest.fixture
def xcode(tmp_path):
    "Create a dummy location for Xcode"
    xcode_location = tmp_path / 'Xcode.app'
    xcode_location.mkdir(parents=True, exist_ok=True)
    return str(xcode_location)


def test_not_installed(tmp_path):
    "If Xcode is not installed, raise an error."
    sub = mock.MagicMock()
    sub.check_output.side_effect = subprocess.CalledProcessError(
        cmd=['xcodebuild', '-version'],
        returncode=1
    )

    # Test a location where Xcode *won't* be installed
    with pytest.raises(BriefcaseCommandError):
        ensure_xcode_is_installed(
            xcode_location=str(tmp_path / 'Xcode.app'),
            sub=sub
        )

    # xcode-select was not invoked
    sub.check_output.assert_not_called()


def test_exists_but_not_installed(xcode):
    "If the Xcode folder exists, but xcodebuild breaks, raise an error."
    sub = mock.MagicMock()
    sub.check_output.side_effect = subprocess.CalledProcessError(
        cmd=['xcodebuild', '-version'],
        returncode=1
    )

    with pytest.raises(BriefcaseCommandError):
        ensure_xcode_is_installed(xcode_location=xcode, sub=sub)

    # xcode-select was invoked
    sub.check_output.assert_called_once_with(
        ['xcodebuild', '-version'],
        universal_newlines=True,
    )


def test_installed_no_minimum_version(xcode):
    "If Xcode is installed, but there's no minimum version, check is satisfied."
    sub = mock.MagicMock()
    sub.check_output.return_value = "Xcode 11.2.1\nBuild version 11B500\n"

    # Check passes without an error.
    ensure_xcode_is_installed(xcode_location=xcode, sub=sub)

    # xcode-select was invoked
    sub.check_output.assert_called_once_with(
        ['xcodebuild', '-version'],
        universal_newlines=True,
    )


@pytest.mark.parametrize(
    'min_version, version',
    [
        # Exact match
        ((11, 2, 1), '11.2.1'),  # Exact match
        ((11, 2), '11.2.0'),  # Exact match, implied revision.
        ((11, ), '11.0.0'),  # Exact match, implied minor version.

        # Rules still work for single digit versions
        ((8, 2, 1), '8.2.1'),  # Exact match
        ((8, 2), '8.2.0'),  # Exact match, implied revision.
        ((8, ), '8.0.0'),  # Exact match, implied minor version.

        # Exceeds version
        ((11, 2, 1), '11.2.5'),  # Exceeds revision requirement
        ((11, 2, 1), '11.3.0'),  # Exceeds minor requirement
        ((11, 2, 1), '12.0.0'),  # Exceeds major requirement

        ((11, 2), '11.2.5'),  # Exceeds implied revision requirement
        ((11, 2), '11.3.0'),  # Exceeds minor requirement
        ((11, 2), '12.0.0'),  # Exceeds major requirement

        ((11, ), '11.2.5'),  # Exceeds implied revision requirement
        ((11, ), '11.3.0'),  # Exceeds implied minor requirement
        ((11, ), '12.0.0'),  # Exceeds major requirement

        # 2 digit version number
        # exact match
        ((11, 2, 0), '11.2'),  # Exact match.
        ((11, 2), '11.2'),  # Exact match, implied revision.
        ((11, ), '11.2'),  # Exact match, implied minor version.

        # exceeds version
        ((11, 1, 1), '11.2'),  # Exact match.
        ((11, 1), '11.2'),  # Exact match, implied revision.
        ((11, ), '11.2'),  # Exact match, implied minor version.
    ]
)
def test_installed_with_minimum_version_success(min_version, version, capsys, xcode):
    "Check XCode can meet a minimum version requirement."
    sub = mock.MagicMock()
    sub.check_output.return_value = "Xcode {version}\nBuild version 11B500\n".format(
        version=version
    )

    # Check passes without an error.
    ensure_xcode_is_installed(
        min_version=min_version,
        xcode_location=xcode,
        sub=sub
    )

    # xcode-select was invoked
    sub.check_output.assert_called_once_with(
        ['xcodebuild', '-version'],
        universal_newlines=True,
    )

    # Make sure the warning wasn't displayed.
    out = capsys.readouterr().out
    assert "WARNING" not in out


@pytest.mark.parametrize(
    'min_version, version',
    [
        ((11, 2, 5), '11.2.1'),  # insufficient revision
        ((11, 3), '11.2.1'),  # Insufficient micro version
        ((12, ), '11.2.1'),  # Insufficient major version

        ((8, 2, 5), '8.2.1'),  # insufficient revision
        ((8, 3), '8.2.1'),  # Insufficient micro version
        ((9, ), '8.2.1'),  # Insufficient major version
    ]
)
def test_installed_with_minimum_version_failure(min_version, version, xcode):
    "Check XCode fail to meet a minimum version requirement."
    sub = mock.MagicMock()
    sub.check_output.return_value = "Xcode {version}\nBuild version 11B500\n".format(
        version=version
    )

    # Check raises an error.
    with pytest.raises(BriefcaseCommandError):
        ensure_xcode_is_installed(
            min_version=min_version,
            xcode_location=xcode,
            sub=sub
        )

    # xcode-select was invoked
    sub.check_output.assert_called_once_with(
        ['xcodebuild', '-version'],
        universal_newlines=True,
    )


def test_unexpected_version_output(capsys, xcode):
    "If xcodebuild returns unexpected output, assume it's ok..."
    sub = mock.MagicMock()
    sub.check_output.return_value = "Wibble Wibble Wibble\n"

    # Check passes without an error...
    ensure_xcode_is_installed(
        min_version=(11, 2, 1),
        xcode_location=xcode,
        sub=sub
    )

    # xcode-select was invoked
    sub.check_output.assert_called_once_with(
        ['xcodebuild', '-version'],
        universal_newlines=True,
    )

    # ...but stdout contains a warning
    out = capsys.readouterr().out
    assert '************' in out
