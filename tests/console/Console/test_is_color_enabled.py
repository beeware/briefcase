from unittest.mock import PropertyMock

import pytest
from rich.console import ColorSystem


@pytest.mark.parametrize(
    "no_color, color_system, is_enabled",
    [
        (False, ColorSystem.TRUECOLOR, True),
        (False, None, False),
        (True, ColorSystem.TRUECOLOR, False),
        (True, None, False),
    ],
)
def test_is_color_enabled(
    raw_console,
    no_color,
    color_system,
    is_enabled,
    monkeypatch,
):
    """Color is enabled/disabled based on no_color and color_system."""
    raw_console._console_impl.no_color = no_color
    monkeypatch.setattr(
        type(raw_console._console_impl),
        "color_system",
        PropertyMock(return_value=color_system),
    )

    # confirm these values to make sure they didn't change somehow...
    assert raw_console._console_impl.no_color is no_color
    assert raw_console._console_impl.color_system is color_system

    assert raw_console.is_color_enabled is is_enabled
