import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import ensure_xcode_is_installed


def test_not_installed():
    "If Xcode is not installed, raise an error."
    sub = mock.MagicMock()
    sub.check_output.side_effect = subprocess.CalledProcessError(
        cmd=['xcodebuild', '-version'],
        returncode=1
    )

    with pytest.raises(BriefcaseCommandError):
        ensure_xcode_is_installed(sub=sub)


def test_installed_no_minimum_version():
    "If Xcode is installed, but there's no minimum version, check is satisfied."
    sub = mock.MagicMock()
    sub.check_output.return_value = "Xcode 11.2.1\nBuild version 11B500\n"

    # Check passes without an error.
    ensure_xcode_is_installed(sub=sub)


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
def test_installed_with_minimum_version_success(min_version, version, capsys):
    "Check XCode can meet a minimum version requirement."
    sub = mock.MagicMock()
    sub.check_output.return_value = "Xcode {version}\nBuild version 11B500\n".format(
        version=version
    )

    # Check passes without an error.
    ensure_xcode_is_installed(min_version=min_version, sub=sub)

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
def test_installed_with_minimum_version_failure(min_version, version):
    "Check XCode fail to meet a minimum version requirement."
    sub = mock.MagicMock()
    sub.check_output.return_value = "Xcode {version}\nBuild version 11B500\n".format(
        version=version
    )

    # Check raises an error.
    with pytest.raises(BriefcaseCommandError):
        ensure_xcode_is_installed(min_version=min_version, sub=sub)


def test_unexpected_version_output(capsys):
    "If xcodebuild returns unexpected output, assume it's ok..."
    sub = mock.MagicMock()
    sub.check_output.return_value = "Wibble Wibble Wibble\n"

    # Check passes without an error...
    ensure_xcode_is_installed(min_version=(11, 2, 1), sub=sub)

    # ...but stdout contains a warning
    out = capsys.readouterr().out
    assert '************' in out
