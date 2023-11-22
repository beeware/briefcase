import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_validate_selection_override_none(new_command):
    """An override of ``None`` fails validation."""
    outcome = new_command.validate_selection_override(
        choices=["one", "two", "three"],
        override_value=None,
    )
    assert outcome is True


def test_validate_selection_override_valid(new_command, capsys):
    """A valid override passes validation."""
    outcome = new_command.validate_selection_override(
        choices=["one", "two", "three"],
        override_value="two",
    )

    assert capsys.readouterr().out == "\nUsing override value 'two'\n"
    assert outcome is True


def test_validate_selection_override_valid_no_input(new_command, capsys):
    """A valid override passes validation and no notification with input disabled."""
    new_command.input.enabled = False

    outcome = new_command.validate_selection_override(
        choices=["one", "two", "three"],
        override_value="two",
    )

    assert capsys.readouterr().out == ""
    assert outcome is True


def test_validate_selection_override_invalid(new_command, capsys):
    """An invalid override fails validation."""
    outcome = new_command.validate_selection_override(
        choices=["one", "two", "three"],
        override_value="four",
    )

    assert capsys.readouterr().out == (
        "\nUsing override value 'four'\n\n" "Invalid value; four\n"
    )
    assert outcome is False


def test_validate_selection_override_invalid_no_input(new_command, capsys):
    """An invalid override with input disabled raises."""
    new_command.input.enabled = False

    with pytest.raises(BriefcaseCommandError, match="Invalid value; four"):
        _ = new_command.validate_selection_override(
            choices=["one", "two", "three"],
            override_value="four",
        )
