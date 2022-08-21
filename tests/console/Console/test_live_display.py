from unittest.mock import MagicMock

import pytest

import briefcase.console


@pytest.fixture
def renderable():
    mock_renderable = MagicMock()
    mock_renderable.live = MagicMock()
    mock_renderable.live.transient = False
    return mock_renderable


@pytest.fixture
def monkeypatched_live_display(monkeypatch):
    """Monkeypatch the instantiation of the Live Display."""
    live_display = MagicMock()
    live_display.return_value = live_display
    monkeypatch.setattr(briefcase.console, "Live", live_display)
    return live_display


def test_live_display_add_new(console, renderable):
    """New renderable is added to Live Display."""
    assert console._live_display_stack.count(renderable) == 0

    console._live_display_add(renderable)

    assert len(console._live_display_stack) == 1
    assert console.is_output_controlled is True
    console._live_display.update.assert_called_once()
    console._live_display.start.assert_called_once()


def test_live_display_add_existing(console, renderable):
    """Existing renderable is not added to Live Display."""
    assert console._live_display_stack.count(renderable) == 0
    console._live_display_add(renderable)

    console._live_display = MagicMock()
    console._live_display_add(renderable)

    assert console._live_display_stack.count(renderable) == 1
    assert len(console._live_display_stack) == 1
    assert console.is_output_controlled is True
    console._live_display.update.assert_not_called()
    console._live_display.start.assert_not_called()


def test_live_display_remove_only_existing(console, renderable):
    """Only existing renderable is removed from Live Display."""
    assert console._live_display_stack.count(renderable) == 0
    console._live_display_add(renderable)

    console._live_display = MagicMock()
    console._live_display_remove(renderable)

    assert len(console._live_display_stack) == 0
    assert console.is_output_controlled is False
    console._live_display.stop.assert_called_once()


def test_live_display_remove_existing(console, renderable):
    """Existing renderable is removed from Live Display."""
    assert console._live_display_stack.count(renderable) == 0
    console._live_display_add(renderable)
    console._live_display_add("asdf")

    console._live_display = MagicMock()
    console._live_display_remove(renderable)

    assert len(console._live_display_stack) == 1
    assert console.is_output_controlled is True
    console._live_display.update.assert_called_once()
    console._live_display.start.assert_called_once()


def test_live_display_remove_nonexistent(console, renderable):
    """Nonexistent renderable is effectively removed from Live Display
    stack."""
    assert console._live_display_stack.count(renderable) == 0
    console._live_display_add("asdf")

    console._live_display = MagicMock()
    console._live_display_remove(renderable)

    assert len(console._live_display_stack) == 1
    assert console.is_output_controlled is True
    console._live_display.update.assert_called_once()
    console._live_display.start.assert_called_once()


def test_live_display_update_new(console, renderable, monkeypatched_live_display):
    """Live Display is created and updated for fresh renderable."""
    console._live_display = None

    console._live_display_add(renderable)

    assert console._live_display is monkeypatched_live_display
    assert console.is_output_controlled is True
    monkeypatched_live_display.update.assert_called_once()
    monkeypatched_live_display.start.assert_called_once()


def test_live_display_remove_dynamic_elements_active(console):
    """Live Display is stopped when removing active dynamic elements."""
    initial_live_display = console._live_display
    console.is_output_controlled = True

    console.remove_dynamic_elements()

    initial_live_display.stop.assert_called_once()
    assert console._live_display is None
    assert console.is_output_controlled is False


def test_live_display_remove_dynamic_elements_not_active(console):
    """Live Display is not stopped when there are no dynamic elements
    active."""
    console._live_display = None
    assert console.is_output_controlled is False

    console.remove_dynamic_elements()

    assert console._live_display is None
    assert console.is_output_controlled is False


def test_live_display_restore_dynamic_elements(console, monkeypatched_live_display):
    """Live Display is updated when restoring any dynamic elements."""
    console._live_display_stack = ["asdf"]
    console._live_display = None
    assert console.is_output_controlled is False

    console.restore_dynamic_elements()

    monkeypatched_live_display.update.assert_called_once()
    monkeypatched_live_display.start.assert_called_once()
    assert console.is_output_controlled is True


def test_live_display_restore_dynamic_elements_no_active(
    console,
    monkeypatched_live_display,
):
    """Live Display is not updated when no dynamic elements to restore."""
    console._live_display = None
    assert console.is_output_controlled is False

    console.restore_dynamic_elements()

    monkeypatched_live_display.update.assert_not_called()
    monkeypatched_live_display.start.assert_not_called()
    monkeypatched_live_display.stop.assert_called_once()
    assert console.is_output_controlled is False


def test_live_display_restore_dynamic_elements_with_existing_live_display(
    console,
    monkeypatched_live_display,
):
    """Live Display is updated when restoring any dynamic elements."""
    # this shouldn't happen in practice since "remove" sets live display to None
    console._live_display_stack = ["asdf"]
    assert console.is_output_controlled is False

    console.restore_dynamic_elements()

    console._live_display.update.assert_called_once()
    console._live_display.start.assert_called_once()
    monkeypatched_live_display.update.assert_not_called()
    monkeypatched_live_display.start.assert_not_called()
    assert console.is_output_controlled is True
