import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS.app import macOSAppPackageCommand


@pytest.fixture
def package_command(tmp_path):
    command = macOSAppPackageCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    return command


@pytest.mark.parametrize(
    "identity_name, team_id",
    [
        ("Developer ID Application: Jane Developer (DEADBEEF)", "DEADBEEF"),
        ("Developer ID Application: Edwin (Buzz) Aldrin (DEADBEEF)", "DEADBEEF"),
    ],
)
def test_team_id_from_identity(package_command, identity_name, team_id):
    assert package_command.team_id_from_identity(identity_name) == team_id


@pytest.mark.parametrize(
    "identity_name",
    [
        "Developer ID Application: Jane Developer",
        "DEADBEEF",
    ],
)
def test_bad_identity(package_command, identity_name):
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Couldn't extract Team ID from signing identity",
    ):
        package_command.team_id_from_identity(identity_name)
