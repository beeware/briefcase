import pytest

from briefcase.console import InputDisabled
from tests.utils import default_rich_prompt


@pytest.mark.parametrize(
    "value, expected",
    [
        ("Value", "Value"),
        ("", "Default"),
    ],
)
def test_text(console, value, expected):
    console.input.return_value = value

    actual = console.text(
        prompt="> ",
        default="Default",
    )

    assert actual == expected
    console.input.assert_called_once_with(default_rich_prompt("> "), markup=True)


def test_disabled(disabled_console):
    """If input is disabled, the default is returned."""
    actual = disabled_console.text(
        prompt="> ",
        default="Default",
    )

    assert actual == "Default"
    disabled_console.input.assert_not_called()


def test_disabled_no_default(disabled_console):
    """If input is disabled and there is no default, an error is raised."""
    with pytest.raises(InputDisabled):
        disabled_console.text(
            prompt="> ",
            default=None,
        )

    disabled_console.input.assert_not_called()
