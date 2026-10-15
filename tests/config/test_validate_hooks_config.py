import pytest

from briefcase.config import validate_hooks_config
from briefcase.exceptions import BriefcaseConfigError


def test_no_hooks():
    """An absent table is an empty table."""
    assert validate_hooks_config("myapp", None) == {}


def test_valid_hooks():
    """Each stage lists commands, each an argument list."""
    hooks = {
        "post_create": [["ruby", "patch.rb"], ["echo", "done"]],
        "pre_build": [],
    }
    assert validate_hooks_config("myapp", hooks) == hooks


def test_hooks_not_a_table():
    """The hooks setting must be a table."""
    with pytest.raises(BriefcaseConfigError, match="must be a table"):
        validate_hooks_config("myapp", ["echo"])


def test_unknown_stage():
    """A stage that does not exist is refused, naming the valid stages."""
    with pytest.raises(
        BriefcaseConfigError,
        match=r"'after_build' is not a hook stage.*pre_create, post_create",
    ):
        validate_hooks_config("myapp", {"after_build": [["echo"]]})


@pytest.mark.parametrize(
    "commands",
    [
        "echo done",  # a string, not a list of commands
        ["echo done"],  # a command as a string
        [[]],  # an empty argument list
        [["echo", 1]],  # a non-string argument
    ],
)
def test_invalid_commands(commands):
    """Each command must be a non-empty list of strings."""
    with pytest.raises(
        BriefcaseConfigError,
        match="post_build hook for app 'myapp' must be a list of commands",
    ):
        validate_hooks_config("myapp", {"post_build": commands})
