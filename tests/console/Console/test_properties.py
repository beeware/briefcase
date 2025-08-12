import os

from briefcase.console import Console


def test_default_constructor(raw_console):
    """A console is enabled by default."""
    assert raw_console.input_enabled


def test_constructor_with_enabled_false():
    """A console can be constructed in a disabled state."""
    try:
        console = Console(input_enabled=False)
        assert not console.input_enabled
    finally:
        console.close()


def test_enable():
    """A disabled console can be enabled."""
    try:
        console = Console(input_enabled=False)
        assert not console.input_enabled

        console.input_enabled = True

        assert console.input_enabled
    finally:
        console.close()


def test_disable(raw_console):
    """A disabled console can be enabled."""
    assert raw_console.input_enabled

    raw_console.input_enabled = False
    assert not raw_console.input_enabled


def test_is_interactive_non_interactive(monkeypatch, raw_console):
    """Console is non-interactive when stdout has no tty."""
    monkeypatch.setattr(os, "isatty", lambda _: False)
    assert raw_console.is_interactive is False


def test_is_interactive_always_interactive(monkeypatch, raw_console):
    """Console is interactive when stdout has a tty."""
    monkeypatch.setattr(os, "isatty", lambda _: True)
    assert raw_console.is_interactive is True
