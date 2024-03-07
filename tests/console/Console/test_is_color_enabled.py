from unittest.mock import PropertyMock

import pytest
from rich.console import ColorSystem

from briefcase.console import Console, Printer


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
    printer = Printer()
    monkeypatch.setattr(
        type(printer.console),
        "color_system",
        PropertyMock(return_value=color_system),
    )
    printer.console.no_color = no_color
    console = Console(printer=printer)

    # confirm these values to make sure they didn't change somehow...
    assert printer.console.no_color is no_color
    assert printer.console.color_system is color_system

    assert console.is_color_enabled is is_enabled
