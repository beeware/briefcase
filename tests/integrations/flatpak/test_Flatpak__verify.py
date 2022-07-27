import subprocess
from unittest import mock

import pytest

from briefcase.console import Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.flatpak import Flatpak


@pytest.fixture
def mock_command(tmp_path):
    command = mock.MagicMock()
    command.logger = Log()
    command.host_arch = "gothic"

    # Mock os and subprocess
    command.subprocess = mock.MagicMock()
    command.os = mock.MagicMock()

    return command


def test_flatpak_not_installed(mock_command):
    """If flatpak isn't installed, an error is raised."""
    # Mock the response from a missing tool
    mock_command.subprocess.check_output.side_effect = FileNotFoundError

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires the Flatpak toolchain, but it does not appear to be installed.",
    ):
        Flatpak.verify(mock_command)

    mock_command.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
        ],
        any_order=False,
    )


def test_flatpak_error(mock_command):
    """If `flatpak --version` fails, an error is raised."""
    # Mock the side effect of an unsuccessful call to flatpak
    mock_command.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd="flatpak --version", returncode=1
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to invoke flatpak.",
    ):
        Flatpak.verify(mock_command)

    mock_command.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
        ],
        any_order=False,
    )


def test_flatpak_old(mock_command):
    """If `flatpak --version` returns an old version, an error is raised."""
    # Mock the side effect of an successful call to an older version of Flatpak
    mock_command.subprocess.check_output.return_value = "Flatpak 0.10.9\n"

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires Flatpak 1.0 or later.",
    ):
        Flatpak.verify(mock_command)

    mock_command.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
        ],
        any_order=False,
    )


def test_flatpak_builder_not_installed(mock_command):
    """If flatpak isn't installed, an error is raised."""
    # Mock the side effect of a call to a missing flatpak-builder
    mock_command.subprocess.check_output.side_effect = [
        "Flatpak 1.12.7",
        FileNotFoundError,
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires the full Flatpak development toolchain, but flatpak-builder",
    ):
        Flatpak.verify(mock_command)

    mock_command.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
            mock.call(["flatpak-builder", "--version"]),
        ],
        any_order=False,
    )


def test_flatpak_builder_error(mock_command):
    """If `flatpak-builder --version` fails, an error is raised."""
    # Mock the side effect of an unsuccessful call to flatpak-builder
    mock_command.subprocess.check_output.side_effect = [
        "Flatpak 1.12.7",
        subprocess.CalledProcessError(cmd="flatpak-builder --version", returncode=1),
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to invoke flatpak-builder.",
    ):
        Flatpak.verify(mock_command)

    mock_command.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
            mock.call(["flatpak-builder", "--version"]),
        ],
        any_order=False,
    )


def test_flatpak_builder_old(mock_command):
    """If the version of flatpak-builder is old, an error is raised."""
    # Mock the side effect of a call to a missing flatpak-builder
    mock_command.subprocess.check_output.side_effect = [
        "Flatpak 1.12.7",
        "flatpak-builder 0.10.9",
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires flatpak-builder 1.0 or later.",
    ):
        Flatpak.verify(mock_command)

    mock_command.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
            mock.call(["flatpak-builder", "--version"]),
        ],
        any_order=False,
    )


def test_installed(mock_command):
    """If flatpak is installed, it can be verified."""
    mock_command.subprocess.check_output.side_effect = [
        "Flatpak 1.12.7",
        "flatpak-builder 1.2.2",
    ]

    flatpak = Flatpak.verify(mock_command)

    mock_command.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
            mock.call(["flatpak-builder", "--version"]),
        ],
        any_order=False,
    )

    # The verified instance is bound to the host architecture.
    assert flatpak.arch == mock_command.host_arch


@pytest.mark.parametrize(
    "flatpak_version",
    [
        # Different tool identification
        "not-flatpak 1.2.2",
        # No version ID
        "Flatpak",
        # Non-integer version ID
        "Flatpak x.y.z",
    ],
)
def test_installed_unknown_flatpak_version(mock_command, flatpak_version, capsys):
    """If flatpak is installed, but the version can't be determined, a warning
    is raised, but flatpak is verified."""
    mock_command.subprocess.check_output.side_effect = [
        flatpak_version,
        "flatpak-builder 1.2.2",
    ]

    flatpak = Flatpak.verify(mock_command)

    mock_command.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
            mock.call(["flatpak-builder", "--version"]),
        ],
        any_order=False,
    )

    # The verified instance is bound to the host architecture.
    assert flatpak.arch == mock_command.host_arch

    output = capsys.readouterr()
    assert "** WARNING: Unable to determine the version of Flatpak" in output.out
    assert output.err == ""


@pytest.mark.parametrize(
    "builder_version",
    [
        # Different tool identification
        "not-flatpak-builder 1.2.2",
        # No version ID
        "flatpak-builder",
        # Non-integer version ID
        "flatpak-builder x.y.z",
    ],
)
def test_installed_unknown_builder_version(mock_command, builder_version, capsys):
    """If flatpak-builder is installed, but the version can't be determined, a
    warning is raised, but flatpak is verified."""
    mock_command.subprocess.check_output.side_effect = [
        "Flatpak 1.12.7",
        builder_version,
    ]

    flatpak = Flatpak.verify(mock_command)

    mock_command.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
            mock.call(["flatpak-builder", "--version"]),
        ],
        any_order=False,
    )

    # The verified instance is bound to the host architecture.
    assert flatpak.arch == mock_command.host_arch

    output = capsys.readouterr()
    assert (
        "** WARNING: Unable to determine the version of flatpak-builder" in output.out
    )
    assert output.err == ""
