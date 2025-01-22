from unittest.mock import PropertyMock

import pytest
from rich.console import ColorSystem

from briefcase.console import Console


@pytest.mark.parametrize(
    "no_color, color_system, is_enabled",
    [
        (False, ColorSystem.TRUECOLOR, True),
        (False, None, False),
        (True, ColorSystem.TRUECOLOR, False),
        (True, None, False),
    ],
)
def test_is_color_enabled(no_color, color_system, is_enabled, monkeypatch):
    """Color is enabled/disabled based on no_color and color_system."""
    console = Console()
    console._console_impl.no_color = no_color
    monkeypatch.setattr(
        type(console._console_impl),
        "color_system",
        PropertyMock(return_value=color_system),
    )

    # confirm these values to make sure they didn't change somehow...
    assert console._console_impl.no_color is no_color
    assert console._console_impl.color_system is color_system

    assert console.is_color_enabled is is_enabled
