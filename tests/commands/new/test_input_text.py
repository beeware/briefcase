import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_unvalidated_input(new_command):
    """If the user enters text and there's no validation, the text is returned."""
    new_command.input.values = ["hello"]

    value = new_command.input_text(
        intro="Some introduction", variable="my variable", default="goodbye"
    )

    assert new_command.input.prompts == ["My Variable [goodbye]: "]
    assert value == "hello"


def test_unvalidated_input_with_override(new_command):
    """If an override is provided and there's no validation, the override is
    returned."""
    new_command.input.values = ["hello"]

    value = new_command.input_text(
        intro="Some introduction",
        variable="my variable",
        default="goodbye",
        override_value="override",
    )

    assert new_command.input.prompts == []
    assert value == "override"


def test_validated_input(new_command):
    """If the user enters text and there's validation, the user is prompted until valid
    text is entered."""
    new_command.input.values = ["bad", "hello"]

    def validator(text):
        if text == "bad":
            raise ValueError("That's bad...")
        return True

    value = new_command.input_text(
        intro="Some introduction",
        variable="my variable",
        default="goodbye",
        validator=validator,
    )

    assert new_command.input.prompts == [
        "My Variable [goodbye]: ",
        "My Variable [goodbye]: ",
    ]
    assert value == "hello"


def test_validated_input_with_override(new_command):
    """If an override is provided and there's validation, the override is validated and
    returned."""

    def validator(text):
        if text == "bad":
            raise ValueError("That's bad...")
        return True

    value = new_command.input_text(
        intro="Some introduction",
        variable="my variable",
        default="goodbye",
        validator=validator,
        override_value="override",
    )

    assert new_command.input.prompts == []
    assert value == "override"


def test_validated_input_with_invalid_override(new_command):
    """If an invalid override is provided and there's validation, the override is
    rejected and the user is prompted until valid text is entered."""
    new_command.input.values = ["bad", "hello"]

    def validator(text):
        if text in {"bad", "bad-override"}:
            return False
        return True

    value = new_command.input_text(
        intro="Some introduction",
        variable="my variable",
        default="goodbye",
        validator=validator,
        override_value="bad-override",
    )

    assert new_command.input.prompts == [
        "My Variable [goodbye]: ",
        "My Variable [goodbye]: ",
    ]
    assert value == "hello"


def test_input_with_default(new_command):
    """If the user enters text and there's no validation, the text is returned."""
    new_command.input.values = [""]

    value = new_command.input_text(
        intro="Some introduction", variable="my variable", default="goodbye"
    )

    assert new_command.input.prompts == ["My Variable [goodbye]: "]
    assert value == "goodbye"


def test_input_disabled(new_command):
    """If input is disabled, the default is returned."""
    new_command.input.enabled = False

    value = new_command.input_text(
        intro="Some introduction",
        variable="my variable",
        default="goodbye",
    )

    assert new_command.input.prompts == []
    assert value == "goodbye"


def test_input_disabled_with_override(new_command):
    """If input is disabled, the override is returned."""
    new_command.input.enabled = False

    value = new_command.input_text(
        intro="Some introduction",
        variable="my variable",
        default="goodbye",
        override_value="override",
    )

    assert new_command.input.prompts == []
    assert value == "override"


def test_input_disabled_validation_failure(new_command):
    """If input is disabled, and validation fails, an error is raised."""
    new_command.input.enabled = False

    with pytest.raises(BriefcaseCommandError, match="Well that won't work..."):

        def not_valid(text):
            raise ValueError("Well that won't work...")

        new_command.input_text(
            intro="Some introduction",
            variable="my variable",
            default="goodbye",
            validator=not_valid,
        )

    assert new_command.input.prompts == []


def test_input_disabled_validation_failure_with_override(new_command):
    """If input is disabled, and validation fails for override, an error is raised."""
    new_command.input.enabled = False

    with pytest.raises(BriefcaseCommandError, match="Well that won't work..."):

        def not_valid(text):
            raise ValueError("Well that won't work...")

        new_command.input_text(
            intro="Some introduction",
            variable="my variable",
            default="goodbye",
            validator=not_valid,
            override_value="override",
        )

    assert new_command.input.prompts == []


def test_prompt_capitalization(new_command):
    """The prompt is capitalized appropriately."""
    new_command.input.values = ["hello"]

    new_command.input_text(
        intro="Some introduction", variable="user's URL", default="goodbye"
    )

    assert new_command.input.prompts == ["User's URL [goodbye]: "]
