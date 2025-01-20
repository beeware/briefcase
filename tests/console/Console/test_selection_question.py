import pytest

from tests.utils import DummyConsole


def test_selection_question():
    "A question with a dictionary of options can be presented to the user."
    console = DummyConsole("3")

    options = {
        "first": "The first option",
        "second": "The second option",
        "third": "The third option",
        "fourth": "The fourth option",
    }
    result = console.selection_question(
        description="Test",
        intro="This is a test",
        options=options,
    )

    # Input is requested once
    assert console.prompts == ["Test: "]

    # "third" is the key of the third option.
    assert result == "third"


def test_selection_question_list():
    """If selection_question is given a list of values, they're presented as provided."""
    # Return '3' when prompted
    console = DummyConsole("3")

    options = [
        "The first option",
        "The second option",
        "The third option",
        "The fourth option",
    ]
    result = console.selection_question(
        description="Test",
        intro="This is a test",
        options=options,
    )

    # Input is requested once
    assert console.prompts == ["Test: "]

    # The third option is the third option :-)
    assert result == "The third option"


def test_selection_question_bad_input():
    # In order, return:
    #     blank
    #     'asdf'
    #     '10'
    #     '3'
    console = DummyConsole("", "asdf", "10", "3")

    options = {
        "first": "The first option",
        "second": "The second option",
        "third": "The third option",
        "fourth": "The fourth option",
    }
    result = console.selection_question(
        description="Test",
        intro="This is a test",
        options=options,
    )

    # Input is requested five times; first four cause errors.
    assert console.prompts == ["Test: "] * 4

    # The third option was eventually selected
    assert result == "third"


@pytest.mark.parametrize("index, default", [("1", "first"), ("3", "third")])
def test_selection_question_default(index, default):
    """If selection_question has a default, it is returned for no input."""
    # Return an empty response when prompted as though the user press entered
    console = DummyConsole("")

    options = {
        "first": "The first option",
        "second": "The second option",
        "third": "The third option",
        "fourth": "The fourth option",
    }
    result = console.selection_question(
        description="Test",
        intro="This is a test",
        options=options,
        default=default,
    )

    # Input is requested once
    assert console.prompts == [f"Test [{index}]: "]

    # The default option is returned
    assert result == default


def test_override_used(capsys):
    """The override is used if valid."""
    console = DummyConsole()

    override_value = "value"
    assert (
        console.selection_question(
            intro="intro",
            description="My variable",
            default=None,
            options=["value", "some_value", "other_value"],
            override_value="value",
        )
        == "value"
    )
    assert f"Using override value {override_value!r}" in capsys.readouterr().out


def test_override_validation(capsys):
    """The override is not used if it is not a valid option."""
    console = DummyConsole("3")

    result = console.selection_question(
        intro="intro",
        description="My variable",
        default="value",
        options=["value", "some_value", "other_value"],
        override_value="invalid_value",
    )

    output = capsys.readouterr().out

    assert "Invalid override value for My variable: 'invalid_value'" in output

    # "other value" was selected by the user after validation failed.
    assert result == "other_value"


def test_default_value_has_correct_index():
    """The default value is used and has the correct index if it is a valid option."""
    console = DummyConsole("")

    result = console.selection_question(
        intro="intro",
        description="My variable",
        default="some_value",
        options=["value", "some_value", "other_value"],
        override_value=None,
    )

    # The result is the default value
    assert result == "some_value"


def test_exception_if_wrong_default():
    """An exception is raised if the default value is not a valid option."""
    console = DummyConsole("")

    with pytest.raises(
        ValueError,
        match=r"'invalid_value' is not a valid default value",
    ):
        console.selection_question(
            intro="intro",
            description="My variable",
            default="invalid_value",
            options=["value", "some_value", "other_value"],
            override_value=None,
        )
