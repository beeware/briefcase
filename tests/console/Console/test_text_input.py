import pytest

from briefcase.console import InputDisabled


@pytest.mark.parametrize(
    "value, expected", [
        ("Value", "Value"),
        ("", "Default"),
    ]
)
def test_text_input(console, value, expected):
    prompt = "> "
    default = "Default"

    console._input.return_value = value

    actual = console.text_input(prompt=prompt, default=default)

    assert actual == expected
    console._input.assert_called_once_with(prompt)


def test_disabled(disabled_console):
    "If input is disabled, the default is returned"
    prompt = "> "

    actual = disabled_console.text_input(prompt=prompt, default="Default")

    assert actual == "Default"
    disabled_console._input.assert_not_called()


def test_disabled_no_default(disabled_console):
    "If input is disabled and there is no default, an error is raised"
    prompt = "> "

    with pytest.raises(InputDisabled):
        disabled_console.text_input(prompt=prompt, default=None)

    disabled_console._input.assert_not_called()
