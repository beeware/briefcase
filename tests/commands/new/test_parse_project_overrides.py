import pytest

from briefcase.commands.new import parse_project_overrides
from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.parametrize(
    "cmdline, overrides",
    [
        ([], {}),
        (["license=MIT"], {"license": "MIT"}),
        (["bootstrap=Toga Automation"], {"bootstrap": "Toga Automation"}),
        (["one=1", "two=2"], {"one": "1", "two": "2"}),
        (["one\n=\n1", "two=\n\n2"], {"one": "1", "two": "2"}),
        (["one==1", "two===2"], {"one": "=1", "two": "==2"}),
        (["   one  = 1  ", " two  =  2 "], {"one": "1", "two": "2"}),
    ],
)
def test_project_overrides(cmdline, overrides):
    """Valid project configuration overrides are parsed correctly."""
    assert parse_project_overrides(cmdline) == overrides


def test_project_overrides_invalid():
    """Invalid project configuration overrides are rejected."""
    with pytest.raises(
        BriefcaseCommandError,
        match="Unable to parse project configuration override ' license '",
    ):
        parse_project_overrides([" license "])


@pytest.mark.parametrize(
    "cmdline",
    [
        "=",
        " = ",
        "key_for_invalid_value=",
        " key_for_invalid_value =   ",
        "=value_for_invalid_key",
        "  = value_for_invalid_key   ",
    ],
)
def test_project_overrides_empty(cmdline):
    """Invalid project configuration overrides are rejected."""
    with pytest.raises(
        BriefcaseCommandError,
        match=f"Invalid Project configuration override '{cmdline}'",
    ):
        parse_project_overrides([cmdline])


def test_project_overrides_duplicate():
    """Duplicate project configuration overrides are rejected."""
    with pytest.raises(
        BriefcaseCommandError,
        match="Project configuration override 'license' specified multiple times",
    ):
        parse_project_overrides(["license=MIT", "license=BSD"])
