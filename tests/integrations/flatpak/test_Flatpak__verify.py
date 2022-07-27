import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.flatpak import Flatpak


@pytest.fixture
def mock_command(tmp_path):
    command = mock.MagicMock()
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


def test_installed(mock_command):
    """If linuxdeploy is installed, it can be verified."""
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
