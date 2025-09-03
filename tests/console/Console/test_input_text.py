import pytest

from briefcase.console import InputDisabled


@pytest.mark.parametrize(
    "value, expected",
    [
        ("Value", "Value"),
        ("", "Default"),
    ],
)
def test_text_question(console, value, expected):
    console.values = [value]

    actual = console.input_text(
        prompt="> ",
        default="Default",
    )

    assert actual == expected
    assert console.prompts == ["> "]


def test_disabled(disabled_console):
    """If input is disabled, the default is returned."""
    actual = disabled_console.input_text(
        prompt="> ",
        default="Default",
    )

    assert actual == "Default"
    assert disabled_console.prompts == []


def test_disabled_no_default(disabled_console):
    """If input is disabled and there is no default, an error is raised."""
    with pytest.raises(InputDisabled):
        disabled_console.input_text(
            prompt="> ",
            default=None,
        )

    assert disabled_console.prompts == []
