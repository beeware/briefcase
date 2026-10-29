from unittest import mock

import pytest

from briefcase.commands.base import BaseCommand
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.iOS.xcode import iOSSigningIdentity, iOSXcodeMixin


class DummyCommand(iOSXcodeMixin, BaseCommand):
    """A dummy command that includes the iOS Xcode mixin."""

    command = "dummy"

    def __init__(self, base_path, **kwargs):
        super().__init__(base_path=base_path, **kwargs)


@pytest.fixture
def dummy_command(dummy_console, tmp_path):
    cmd = DummyCommand(
        console=dummy_console,
        base_path=tmp_path,
    )

    cmd.get_identities = mock.MagicMock(
        return_value={
            "11111111111111111111111111111111111111AA": (
                "Developer ID Application: Jane Developer (TEAM123456)"
            ),
            "22222222222222222222222222222222222222BB": (
                "Apple Development: jane@example.com (MEMBER1234)"
            ),
            "33333333333333333333333333333333333333CC": (
                "Apple Distribution: Jane Developer (TEAM123456)"
            ),
            "44444444444444444444444444444444444444DD": (
                "iPhone Developer: jane@example.com (MEMBER5678)"
            ),
        }
    )
    cmd.get_team_id = mock.MagicMock(return_value="TEAM123456")

    return cmd


def test_select_identity(dummy_command, capsys):
    """If no identity is specified, the user selects from the development identities."""
    # Select the second development identity
    dummy_command.console.values = ["2"]

    identity = dummy_command.select_identity()

    assert identity == iOSSigningIdentity(
        id="44444444444444444444444444444444444444DD",
        name="iPhone Developer: jane@example.com (MEMBER5678)",
        team_id="TEAM123456",
    )

    # Only development identities were offered.
    output = capsys.readouterr().out
    assert "1) Apple Development: jane@example.com (MEMBER1234)" in output
    assert "2) iPhone Developer: jane@example.com (MEMBER5678)" in output
    assert "3)" not in output

    # The team ID was obtained for the selected identity.
    dummy_command.get_team_id.assert_called_once_with(
        dummy_command.tools,
        "44444444444444444444444444444444444444DD",
        "iPhone Developer: jane@example.com (MEMBER5678)",
    )


@pytest.mark.parametrize(
    "identity",
    [
        "22222222222222222222222222222222222222BB",
        "Apple Development: jane@example.com (MEMBER1234)",
    ],
)
def test_explicit_identity(dummy_command, identity):
    """An identity can be specified by fingerprint or name."""
    assert dummy_command.select_identity(identity) == iOSSigningIdentity(
        id="22222222222222222222222222222222222222BB",
        name="Apple Development: jane@example.com (MEMBER1234)",
        team_id="TEAM123456",
    )

    # User input was not solicited
    assert dummy_command.console.prompts == []


@pytest.mark.parametrize(
    "identity",
    [
        "DEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEF",
        # Valid, but not a development identity
        "Developer ID Application: Jane Developer (TEAM123456)",
    ],
)
def test_invalid_identity(dummy_command, identity):
    """If the specified identity isn't a development identity, an error is raised."""
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Invalid development signing identity",
    ):
        dummy_command.select_identity(identity)


def test_ambiguous_identity(dummy_command):
    """If more than one identity has the specified name, an error is raised."""
    # A renewed certificate has the same name as the original.
    dummy_command.get_identities.return_value[
        "55555555555555555555555555555555555555EE"
    ] = "Apple Development: jane@example.com (MEMBER1234)"

    with pytest.raises(
        BriefcaseCommandError,
        match=r"More than one signing identity is named",
    ):
        dummy_command.select_identity(
            "Apple Development: jane@example.com (MEMBER1234)"
        )


def test_no_development_identities(dummy_command):
    """If there are no development identities, an error is raised."""
    dummy_command.get_identities.return_value = {
        "11111111111111111111111111111111111111AA": (
            "Developer ID Application: Jane Developer (TEAM123456)"
        ),
    }

    with pytest.raises(
        BriefcaseCommandError,
        match=r"No development signing identities are available",
    ):
        dummy_command.select_identity()
