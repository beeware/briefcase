from importlib import metadata
from unittest.mock import MagicMock

import pytest

from briefcase.bootstraps import (
    ConsoleBootstrap,
    EmptyBootstrap,
    PygameGuiBootstrap,
    PySide6GuiBootstrap,
    TogaGuiBootstrap,
)


def test_question_sequence_toga(new_command):
    """The Toga bootstrap can be selected."""
    new_command.console.values = [
        "1",  # Toga GUI toolkit
    ]

    bootstrap_class = new_command.select_bootstrap(project_overrides={})

    assert bootstrap_class is TogaGuiBootstrap


def test_question_sequence_console(new_command):
    """A console bootstrap can be constructed."""
    new_command.console.values = [
        "4",  # Console app
    ]

    bootstrap_class = new_command.select_bootstrap(project_overrides={})

    assert bootstrap_class is ConsoleBootstrap


def test_question_sequence_pyside6(new_command):
    """A PySide6 bootstrap can be created."""
    new_command.console.values = [
        "2",  # PySide6 app
    ]

    bootstrap_class = new_command.select_bootstrap(project_overrides={})

    assert bootstrap_class is PySide6GuiBootstrap


def test_question_sequence_pygame(new_command):
    """A Pygame bootstrap can be constructed."""
    new_command.console.values = [
        "3",  # PyGame
    ]

    bootstrap_class = new_command.select_bootstrap(project_overrides={})

    assert bootstrap_class is PygameGuiBootstrap


def test_question_sequence_none(new_command):
    """If no bootstrap is selected, the empty bootstrap is used."""
    new_command.console.values = [
        "6",  # No toolkit
    ]

    bootstrap_class = new_command.select_bootstrap(project_overrides={})

    assert bootstrap_class is EmptyBootstrap


def test_question_sequence_other_framework(new_command, capsys):
    """Selecting 'Other frameworks' shows guidance and aborts cleanly."""
    new_command.console.values = [
        "5",  # Other framework
        "1",  # The first community framework (Toga Positron)
    ]

    with pytest.raises(SystemExit) as excinfo:
        new_command.select_bootstrap(project_overrides={})

    assert excinfo.value.code == 0

    out = capsys.readouterr().out

    assert "1) Toga Positron: " in out
    assert "2) Pygame-ce: " in out
    assert "3) No GUI framework" in out

    # And install instructions were displayed
    assert "python -m pip install toga-positron" in out


def test_question_sequence_other_none(new_command, capsys):
    """'None' can be selected from the 'Other frameworks' menu."""
    new_command.console.values = [
        "5",  # Other framework
        "3",  # No framework selected from the "other" menu
    ]

    bootstrap_class = new_command.select_bootstrap(project_overrides={})

    out = capsys.readouterr().out

    assert "1) Toga Positron: " in out
    assert "2) Pygame-ce: " in out
    assert "3) No GUI framework" in out

    # Empty bootstrap was selected.
    assert bootstrap_class is EmptyBootstrap


def test_other_frameworks_hide_installed(new_command, capsys, monkeypatch):
    """Installed community bootstraps are not shown in the submenu."""

    # Fake the installation of pygame-ce
    def _metadata(package_name):
        if package_name == "pygame-ce":
            return
        raise metadata.PackageNotFoundError()

    monkeypatch.setattr(metadata, "metadata", MagicMock(side_effect=_metadata))

    new_command.console.values = [
        "5",  # Other framework
        "1",  # The first community framework (Toga Positron)
    ]

    with pytest.raises(SystemExit) as excinfo:
        new_command.select_bootstrap(project_overrides={})

    assert excinfo.value.code == 0

    out = capsys.readouterr().out

    assert "1) Toga Positron: " in out
    assert "2) No GUI framework" in out

    # Pygame-ce doesn't appear
    assert "Pygame-ce: " not in out


def test_other_frameworks_all_installed(new_command, capsys, monkeypatch):
    """If all community GUI bootstraps are installed, a warning is shown."""

    # Fake the installation of all plugins
    def _metadata(package_name):
        return

    monkeypatch.setattr(metadata, "metadata", MagicMock(side_effect=_metadata))

    new_command.console.values = [
        "5",  # Other framework
        "1",  # The first community framework (Toga Positron)
    ]

    bootstrap_class = new_command.select_bootstrap(project_overrides={})

    out = capsys.readouterr().out

    # The user is warned there are no more bootstraps
    assert "All known community GUI bootstraps are currently installed." in out

    # The only menu option is "nothing"
    assert "1) No GUI framework" in out

    # No community plugin appears
    assert "Toga Positron: " not in out
    assert "Pygame-ce: " not in out

    assert bootstrap_class is EmptyBootstrap


def test_question_sequence_with_overrides(new_command, monkeypatch):
    """The answer to the bootstrap question can be overridden."""

    bootstrap_class = new_command.select_bootstrap(
        project_overrides={"bootstrap": "Toga"}
    )

    assert bootstrap_class is TogaGuiBootstrap


def test_question_sequence_with_bad_bootstrap_override(new_command, monkeypatch):
    """A bad override for the bootstrap uses user input instead."""

    # Simulate user selecting Toga from the menu after bad override.
    new_command.console.values = [
        "1",  # Toga
    ]

    bootstrap_class = new_command.select_bootstrap(
        project_overrides={"bootstrap": "BAD I don't exist GUI"}
    )

    assert bootstrap_class is TogaGuiBootstrap


def test_question_sequence_with_no_user_input(new_command):
    """If no user input is provided, all user inputs are taken as default."""

    new_command.console.input_enabled = False

    bootstrap_class = new_command.select_bootstrap(project_overrides={})

    assert bootstrap_class is TogaGuiBootstrap
