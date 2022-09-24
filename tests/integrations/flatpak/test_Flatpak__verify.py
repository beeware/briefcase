import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.flatpak import Flatpak


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.flatpak = "tool"

    tool = Flatpak.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.flatpak


def test_flatpak_not_installed(mock_tools):
    """If flatpak isn't installed, an error is raised."""
    # Mock the response from a missing tool
    mock_tools.subprocess.check_output.side_effect = FileNotFoundError

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires the Flatpak toolchain, but it does not appear to be installed.",
    ):
        Flatpak.verify(mock_tools)

    mock_tools.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
        ],
        any_order=False,
    )


def test_flatpak_error(mock_tools):
    """If `flatpak --version` fails, an error is raised."""
    # Mock the side effect of an unsuccessful call to flatpak
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd="flatpak --version", returncode=1
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to invoke flatpak.",
    ):
        Flatpak.verify(mock_tools)

    mock_tools.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
        ],
        any_order=False,
    )


def test_flatpak_old(mock_tools):
    """If `flatpak --version` returns an old version, an error is raised."""
    # Mock the side effect of a successful call to an older version of Flatpak
    mock_tools.subprocess.check_output.return_value = "Flatpak 0.10.9\n"

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires Flatpak 1.0 or later.",
    ):
        Flatpak.verify(mock_tools)

    mock_tools.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
        ],
        any_order=False,
    )


def test_flatpak_builder_not_installed(mock_tools):
    """If flatpak isn't installed, an error is raised."""
    # Mock the side effect of a call to a missing flatpak-builder
    mock_tools.subprocess.check_output.side_effect = [
        "Flatpak 1.12.7",
        FileNotFoundError,
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires the full Flatpak development toolchain, but flatpak-builder",
    ):
        Flatpak.verify(mock_tools)

    mock_tools.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
            mock.call(["flatpak-builder", "--version"]),
        ],
        any_order=False,
    )


def test_flatpak_builder_error(mock_tools):
    """If `flatpak-builder --version` fails, an error is raised."""
    # Mock the side effect of an unsuccessful call to flatpak-builder
    mock_tools.subprocess.check_output.side_effect = [
        "Flatpak 1.12.7",
        subprocess.CalledProcessError(cmd="flatpak-builder --version", returncode=1),
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to invoke flatpak-builder.",
    ):
        Flatpak.verify(mock_tools)

    mock_tools.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
            mock.call(["flatpak-builder", "--version"]),
        ],
        any_order=False,
    )


def test_flatpak_builder_old(mock_tools):
    """If the version of flatpak-builder is old, an error is raised."""
    # Mock the side effect of a call to a missing flatpak-builder
    mock_tools.subprocess.check_output.side_effect = [
        "Flatpak 1.12.7",
        "flatpak-builder 0.10.9",
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires flatpak-builder 1.0 or later.",
    ):
        Flatpak.verify(mock_tools)

    mock_tools.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
            mock.call(["flatpak-builder", "--version"]),
        ],
        any_order=False,
    )


def test_installed(mock_tools):
    """If flatpak is installed, it can be verified."""
    mock_tools.subprocess.check_output.side_effect = [
        "Flatpak 1.12.7",
        "flatpak-builder 1.2.2",
    ]

    Flatpak.verify(mock_tools)

    mock_tools.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
            mock.call(["flatpak-builder", "--version"]),
        ],
        any_order=False,
    )


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
def test_installed_unknown_flatpak_version(mock_tools, flatpak_version, capsys):
    """If flatpak is installed, but the version can't be determined, a warning
    is raised, but flatpak is verified."""
    mock_tools.subprocess.check_output.side_effect = [
        flatpak_version,
        "flatpak-builder 1.2.2",
    ]

    Flatpak.verify(mock_tools)

    mock_tools.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
            mock.call(["flatpak-builder", "--version"]),
        ],
        any_order=False,
    )

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
def test_installed_unknown_builder_version(mock_tools, builder_version, capsys):
    """If flatpak-builder is installed, but the version can't be determined, a
    warning is raised, but flatpak is verified."""
    mock_tools.subprocess.check_output.side_effect = [
        "Flatpak 1.12.7",
        builder_version,
    ]

    Flatpak.verify(mock_tools)

    mock_tools.subprocess.check_output.assert_has_calls(
        [
            mock.call(["flatpak", "--version"]),
            mock.call(["flatpak-builder", "--version"]),
        ],
        any_order=False,
    )

    output = capsys.readouterr()
    assert (
        "** WARNING: Unable to determine the version of flatpak-builder" in output.out
    )
    assert output.err == ""
