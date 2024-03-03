from unittest.mock import MagicMock

import pytest

import briefcase.commands.new


@pytest.fixture
def mock_select_option(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(briefcase.commands.new, "_select_option", mock)
    return mock


def test_override_used(new_command, capsys):
    """The override is used if valid."""
    override_value = "value"
    assert (
        new_command.select_option(
            intro="intro",
            variable="variable",
            default=None,
            options=["value", "some_value", "other_value"],
            override_value="value",
        )
        == "value"
    )
    assert f"Using override value {override_value!r}" in capsys.readouterr().out


def test_override_validation(new_command, mock_select_option, capsys):
    """The override is not used if it is not a valid option."""
    new_command.select_option(
        intro="intro",
        variable="variable",
        default="value",
        options=["value", "some_value", "other_value"],
        override_value="invalid_value",
    )
    assert (
        "Invalid override value 'invalid_value' for Variable, using user-provided value."
        in capsys.readouterr().out
    )
    mock_select_option.assert_called_once_with(
        prompt="Variable [1]:",
        input=new_command.input,
        default="1",
        options=[
            ("value", "value"),
            ("some_value", "some_value"),
            ("other_value", "other_value"),
        ],
    )


def test_default_value_has_correct_index(new_command, mock_select_option):
    """The default value is used and has the correct index if it is a valid option."""
    new_command.select_option(
        intro="intro",
        variable="variable",
        default="some_value",
        options=["value", "some_value", "other_value"],
        override_value=None,
    )
    mock_select_option.assert_called_once_with(
        prompt="Variable [2]:",
        input=new_command.input,
        default="2",
        options=[
            ("value", "value"),
            ("some_value", "some_value"),
            ("other_value", "other_value"),
        ],
    )


def test_default_default_is_one(new_command, mock_select_option):
    """The default value is 1 if it is not provided."""
    new_command.select_option(
        intro="intro",
        variable="variable",
        default=None,
        options=["value", "some_value", "other_value"],
        override_value=None,
    )
    mock_select_option.assert_called_once_with(
        prompt="Variable [1]:",
        input=new_command.input,
        default="1",
        options=[
            ("value", "value"),
            ("some_value", "some_value"),
            ("other_value", "other_value"),
        ],
    )


def test_exception_if_wrong_default(new_command, mock_select_option):
    """An exception is raised if the default value is not a valid option."""
    with pytest.raises(ValueError):
        new_command.select_option(
            intro="intro",
            variable="variable",
            default="invalid_value",
            options=["value", "some_value", "other_value"],
            override_value=None,
        )
