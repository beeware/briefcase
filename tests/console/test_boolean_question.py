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

    assert console.prompts == ["Confirm? y/n? "]
    assert result is True


def test_boolean_question_no():
    """Test that boolean_question returns False when user selects No."""
    console = DummyConsole("n")

    result = console.boolean_question(
        description="Confirm?",
        intro="Are you sure?",
        default=None,
    )

    assert console.prompts == ["Confirm? y/n? "]
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


def test_boolean_question_invalid_input():
    """Test boolean_question handles invalid input"""
    console = DummyConsole("maybe", "asdf", "y")

    with pytest.raises(
        ValueError,
        match=re.escape("Invalid override value for Confirm?: must be True or False"),
    ):
        console.boolean_question(
            description="Confirm?",
            intro="Are you sure?",
            default=True,
            override_value="invalid_value",
        )


def test_boolean_question_override_used(capsys):
    """The override is used if provided and valid."""
    console = DummyConsole()

    override_value = True
    result = console.boolean_question(
        description="Confirm?",
        intro="Are you sure?",
        default=None,
        override_value=override_value,
    )

    output = capsys.readouterr().out
    assert f"Using override value {override_value!r}" in output
    assert result is True
    assert console.prompts == []


def test_boolean_question_override_invalid():
    """If override_value is invalid, an error should be raised immediately."""
    console = DummyConsole()

    with pytest.raises(
        ValueError,
        match=re.escape("Invalid override value for Confirm?: must be True or False"),
    ):
        console.boolean_question(
            description="Confirm?",
            intro="Are you sure?",
            default=True,
            override_value="invalid_value",
        )


def test_boolean_question_exception_if_wrong_default():
    """An exception is raised if the default value is not a valid boolean."""
    console = DummyConsole("")

    with pytest.raises(
        ValueError,
        match=r"'invalid_value' is not a valid default value for Confirm?",
    ):
        console.boolean_question(
            description="Confirm?",
            intro="Are you sure?",
            default="invalid_value",
        )
