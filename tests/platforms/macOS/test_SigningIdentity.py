import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS import SigningIdentity


@pytest.mark.parametrize(
    "identity_id, identity_name, team_id",
    [
        ("CAFEBEEF", "Developer ID Application: Jane Developer (DEADBEEF)", "DEADBEEF"),
        (
            "CAFEBEEF",
            "Developer ID Application: Edwin (Buzz) Aldrin (DEADBEEF)",
            "DEADBEEF",
        ),
    ],
)
def test_identity(identity_id, identity_name, team_id):
    """A signing identity can be created."""
    identity = SigningIdentity(id=identity_id, name=identity_name)
    assert identity.id == identity_id
    assert identity.name == identity_name
    assert identity.team_id == team_id
    assert not identity.is_adhoc
    assert repr(identity) == f"<SigningIdentity id={identity_id}>"


@pytest.mark.parametrize(
    "identity_name",
    [
        "Developer ID Application: Jane Developer",
        "DEADBEEF",
    ],
)
def test_bad_identity(identity_name):
    """Creating a bad identity raises an error."""
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Couldn't extract Team ID from signing identity",
    ):
        SigningIdentity(id="CAFEBEEF", name=identity_name)


def test_adhoc_identity():
    """An ad-hoc identity can be created."""
    adhoc = SigningIdentity()
    assert adhoc.id == "-"
    assert (
        adhoc.name
        == "Ad-hoc identity. The resulting package will run but cannot be re-distributed."
    )
    assert adhoc.is_adhoc
    assert repr(adhoc) == "<AdhocSigningIdentity>"
