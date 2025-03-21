import re

import pytest

from tests.utils import DummyConsole


def test_boolean_question_yes():
    """Test that boolean_question returns True when user selects Yes."""
    console = DummyConsole("y")

    result = console.boolean_question(
        description="Confirm?",
        intro="Are you sure?",
        default=None,
    )

    assert console.prompts == ["Confirm? [y/n]? "]
    assert result is True


def test_boolean_question_no():
    """Test that boolean_question returns False when user selects No."""
    console = DummyConsole("n")

    result = console.boolean_question(
        description="Confirm?",
        intro="Are you sure?",
        default=None,
    )

    assert console.prompts == ["Confirm? [y/n]? "]
    assert result is False


@pytest.mark.parametrize(
    "default, expected, prompt",
    [
        (True, True, "Confirm? [Y/n]? "),
        (False, False, "Confirm? [y/N]? "),
    ],
)
def test_boolean_question_default_used(default, expected, prompt):
    """If no input is provided, the default value should be used."""
    console = DummyConsole("")

    result = console.boolean_question(
        description="Confirm?",
        intro="Are you sure?",
        default=default,
    )

    assert console.prompts == [prompt]
    assert result == expected


@pytest.mark.parametrize(
    "override_value, expected_result",
    [
        ("Yes", True),
        ("no", False),
    ],
)
def test_boolean_question_override_used(capsys, override_value, expected_result):
    """The override is used if provided and valid (parametrized for True/False cases)."""
    console = DummyConsole()

    result = console.boolean_question(
        description="Confirm?",
        intro="Are you sure?",
        default=None,
        override_value=override_value,
    )

    output = capsys.readouterr().out
    assert f"Using override value {override_value!r}" in output
    assert result == expected_result
    assert console.prompts == []


def test_boolean_question_override_invalid():
    """If override_value is invalid, an error should be raised immediately."""
    console = DummyConsole()

    with pytest.raises(
        ValueError,
        match=re.escape("Invalid boolean value: 'Yeah Nah'. Expected one of "),
    ):
        console.boolean_question(
            description="Confirm?",
            intro="Are you sure?",
            default=True,
            override_value="Yeah Nah",
        )


def test_boolean_question_empty_input_no_default_returns_false():
    """Reprompts the user when no override or default given"""
    console = DummyConsole("", "", "n")  # Simulates pressing Enter

    result = console.boolean_question(
        description="Confirm?",
        intro="Are you sure?",
        default=None,
        override_value=None,
    )

    assert result is False
