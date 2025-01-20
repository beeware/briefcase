import pytest

from briefcase.exceptions import InputDisabled
from tests.utils import DummyConsole


def test_unvalidated_input():
    """If the user enters text and there's no validation, the text is returned."""
    console = DummyConsole("hello")

    value = console.text_question(
        intro="Some introduction",
        description="My variable",
        default="goodbye",
    )

    assert console.prompts == ["My variable [goodbye]: "]
    assert value == "hello"


def test_unvalidated_input_with_override():
    """If an override is provided and there's no validation, the override is
    returned."""
    console = DummyConsole("hello")

    value = console.text_question(
        intro="Some introduction",
        description="My variable",
        default="goodbye",
        override_value="override",
    )

    assert console.prompts == []
    assert value == "override"


def test_validated_input():
    """If the user enters text and there's validation, the user is prompted until valid
    text is entered."""
    console = DummyConsole("bad", "hello")

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


def test_validated_input_with_override():
    """If an override is provided and there's validation, the override is validated and
    returned."""
    console = DummyConsole()

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


def test_validated_input_with_invalid_override():
    """If an invalid override is provided and there's validation, the override is
    rejected and the user is prompted until valid text is entered."""
    console = DummyConsole("bad", "hello")

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


def test_input_with_default():
    """If the user enters text and there's no validation, the text is returned."""
    console = DummyConsole("")

    value = console.text_question(
        intro="Some introduction", description="My variable", default="goodbye"
    )

    assert console.prompts == ["My variable [goodbye]: "]
    assert value == "goodbye"


def test_input_disabled():
    """If input is disabled, the default is returned."""
    console = DummyConsole(input_enabled=False)

    value = console.text_question(
        intro="Some introduction",
        description="My variable",
        default="goodbye",
    )

    assert console.prompts == []
    assert value == "goodbye"


def test_input_disabled_with_override():
    """If input is disabled, the override is returned."""
    console = DummyConsole(input_enabled=False)

    value = console.text_question(
        intro="Some introduction",
        description="My variable",
        default="goodbye",
        override_value="override",
    )

    assert console.prompts == []
    assert value == "override"


def test_input_disabled_validation_failure():
    """If input is disabled, and validation fails, an error is raised."""
    console = DummyConsole(input_enabled=False)

    with pytest.raises(InputDisabled, match=r"Well that won't work..."):

        def not_valid(text):
            raise ValueError("Well that won't work...")

        console.text_question(
            intro="Some introduction",
            description="My variable",
            default="goodbye",
            validator=not_valid,
        )

    assert console.prompts == []


def test_input_disabled_validation_failure_with_override():
    """If input is disabled, and validation fails for override, an error is raised."""
    console = DummyConsole(input_enabled=False)

    with pytest.raises(InputDisabled, match=r"Well that won't work..."):

        def not_valid(text):
            raise ValueError("Well that won't work...")

        console.text_question(
            intro="Some introduction",
            description="My variable",
            default="goodbye",
            validator=not_valid,
            override_value="override",
        )

    assert console.prompts == []
