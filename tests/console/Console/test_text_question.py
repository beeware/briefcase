import pytest

from briefcase.exceptions import InputDisabled


def test_unvalidated_input(console):
    """If the user enters text and there's no validation, the text is returned."""
    console.values = ["hello"]

    value = console.text_question(
        intro="Some introduction",
        description="My variable",
        default="goodbye",
    )

    assert console.prompts == ["My variable [goodbye]: "]
    assert value == "hello"


def test_unvalidated_input_with_override(console):
    """If an override is provided and there's no validation, the override is
    returned."""
    console.values = ["hello"]

    value = console.text_question(
        intro="Some introduction",
        description="My variable",
        default="goodbye",
        override_value="override",
    )

    assert console.prompts == []
    assert value == "override"


def test_validated_input(console):
    """If the user enters text and there's validation, the user is prompted until valid
    text is entered."""
    console.values = ["bad", "hello"]

    def validator(text):
        if text == "bad":
            raise ValueError("That's bad...")
        return True

    value = console.text_question(
        intro="Some introduction",
        description="My variable",
        default="goodbye",
        validator=validator,
    )

    assert console.prompts == [
        "My variable [goodbye]: ",
        "My variable [goodbye]: ",
    ]
    assert value == "hello"


def test_validated_input_with_override(console):
    """If an override is provided and there's validation, the override is validated and
    returned."""

    def validator(text):
        if text == "bad":
            raise ValueError("That's bad...")
        return True

    value = console.text_question(
        intro="Some introduction",
        description="My variable",
        default="goodbye",
        validator=validator,
        override_value="override",
    )

    assert console.prompts == []
    assert value == "override"


def test_validated_input_with_invalid_override(console):
    """If an invalid override is provided and there's validation, the override is
    rejected and the user is prompted until valid text is entered."""
    console.values = ["bad", "hello"]

    def validator(text):
        if text in {"bad", "bad-override"}:
            return False
        return True

    value = console.text_question(
        intro="Some introduction",
        description="My variable",
        default="goodbye",
        validator=validator,
        override_value="bad-override",
    )

    assert console.prompts == [
        "My variable [goodbye]: ",
        "My variable [goodbye]: ",
    ]
    assert value == "hello"


def test_input_with_default(console):
    """If the user enters text and there's no validation, the text is returned."""
    console.values = [""]

    value = console.text_question(
        intro="Some introduction", description="My variable", default="goodbye"
    )

    assert console.prompts == ["My variable [goodbye]: "]
    assert value == "goodbye"


def test_input_disabled(disabled_console):
    """If input is disabled, the default is returned."""

    value = disabled_console.text_question(
        intro="Some introduction",
        description="My variable",
        default="goodbye",
    )

    assert disabled_console.prompts == []
    assert value == "goodbye"


def test_input_disabled_with_override(disabled_console):
    """If input is disabled, the override is returned."""
    value = disabled_console.text_question(
        intro="Some introduction",
        description="My variable",
        default="goodbye",
        override_value="override",
    )

    assert disabled_console.prompts == []
    assert value == "override"


def test_input_disabled_validation_failure(disabled_console):
    """If input is disabled, and validation fails, an error is raised."""

    def not_valid(text):
        raise ValueError("Well that won't work...")

    with pytest.raises(InputDisabled, match=r"Well that won't work..."):
        disabled_console.text_question(
            intro="Some introduction",
            description="My variable",
            default="goodbye",
            validator=not_valid,
        )

    assert disabled_console.prompts == []


def test_input_disabled_validation_failure_with_override(disabled_console):
    """If input is disabled, and validation fails for override, an error is raised."""

    def not_valid(text):
        raise ValueError("Well that won't work...")

    with pytest.raises(InputDisabled, match=r"Well that won't work..."):
        disabled_console.text_question(
            intro="Some introduction",
            description="My variable",
            default="goodbye",
            validator=not_valid,
            override_value="override",
        )

    assert disabled_console.prompts == []
