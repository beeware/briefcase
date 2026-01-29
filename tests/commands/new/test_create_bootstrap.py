from collections.abc import Collection
from unittest.mock import MagicMock

import pytest

import briefcase.commands.new
from briefcase.bootstraps import (
    BaseGuiBootstrap,
    ConsoleBootstrap,
    EmptyBootstrap,
    PygameGuiBootstrap,
    PySide6GuiBootstrap,
    TogaGuiBootstrap,
)


@pytest.fixture
def mock_builtin_bootstraps():
    return {
        "None": EmptyBootstrap,
        "Toga": TogaGuiBootstrap,
        "Console": ConsoleBootstrap,
        "PySide6": PySide6GuiBootstrap,
        "Pygame": PygameGuiBootstrap,
    }


def test_question_sequence_bootstrap_context(
    new_command,
    mock_builtin_bootstraps,
    monkeypatch,
):
    """The context passed to the bootstrap is correct."""

    passed_context = {}

    class GuiBootstrap:
        fields: Collection[str] = []

        def __init__(self, console, context):
            nonlocal passed_context
            passed_context = context.copy()

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstraps",
        MagicMock(
            return_value={
                **mock_builtin_bootstraps,
                "Custom GUI": GuiBootstrap,
            },
        ),
    )

    new_command.console.input_enabled = False

    bootstrap = new_command.create_bootstrap(
        context={
            "app_name": "myapplication",
            "author": "Grace Hopper",
        },
        project_overrides={
            "bootstrap": "Custom GUI",
        },
    )

    assert isinstance(bootstrap, GuiBootstrap)
    assert passed_context == {
        "app_name": "myapplication",
        "author": "Grace Hopper",
    }


def test_question_sequence_toga(new_command):
    """The Toga bootstrap can be selected."""

    new_command.console.values = [
        "1",  # Toga GUI toolkit
    ]

    bootstrap = new_command.create_bootstrap(
        context={
            "app_name": "myapplication",
            "author": "Grace Hopper",
        },
        project_overrides={},
    )

    assert isinstance(bootstrap, TogaGuiBootstrap)
    assert bootstrap.context == {
        "app_name": "myapplication",
        "author": "Grace Hopper",
    }


def test_question_sequence_console(new_command):
    """A console bootstrap can be constructed."""

    new_command.console.values = [
        "4",  # Console app
    ]

    bootstrap = new_command.create_bootstrap(
        context={
            "app_name": "myapplication",
            "author": "Grace Hopper",
        },
        project_overrides={},
    )

    assert isinstance(bootstrap, ConsoleBootstrap)
    assert bootstrap.context == {
        "app_name": "myapplication",
        "author": "Grace Hopper",
    }


def test_question_sequence_pyside6(new_command):
    """A Pyside6 bootstrap can be created."""

    new_command.console.values = [
        "2",  # PySide6 GUI toolkit
    ]

    bootstrap = new_command.create_bootstrap(
        context={
            "app_name": "myapplication",
            "author": "Grace Hopper",
        },
        project_overrides={},
    )

    assert isinstance(bootstrap, PySide6GuiBootstrap)
    assert bootstrap.context == {
        "app_name": "myapplication",
        "author": "Grace Hopper",
    }


def test_question_sequence_pygame(new_command):
    """A Pygame bootstrap can be constructed."""

    new_command.console.values = [
        "3",  # Pygame GUI toolkit
    ]

    bootstrap = new_command.create_bootstrap(
        context={
            "app_name": "myapplication",
            "author": "Grace Hopper",
        },
        project_overrides={},
    )

    assert isinstance(bootstrap, PygameGuiBootstrap)
    assert bootstrap.context == {
        "app_name": "myapplication",
        "author": "Grace Hopper",
    }


def test_question_sequence_none(new_command):
    """If no bootstrap is selected, the empty bootstrap is used."""

    # Determine the menu index for "None" dynamically, since installed GUI
    # bootstraps can change the menu ordering.
    bootstraps = briefcase.commands.new.get_gui_bootstraps()
    choices = new_command._gui_bootstrap_choices(bootstraps)
    none_index = list(choices.keys()).index("None") + 1

    new_command.console.values = [
        str(none_index),  # None
    ]

    bootstrap = new_command.create_bootstrap(
        context={
            "app_name": "myapplication",
            "author": "Grace Hopper",
        },
        project_overrides={},
    )

    assert isinstance(bootstrap, EmptyBootstrap)
    assert bootstrap.context == {
        "app_name": "myapplication",
        "author": "Grace Hopper",
    }


def test_question_sequence_other_frameworks_aborts(new_command, capsys):
    """Selecting 'Other frameworks…' shows guidance and aborts cleanly."""

    # Determine the menu index for the sentinel entry, since installed
    # GUI bootstraps can change menu ordering.
    bootstraps = briefcase.commands.new.get_gui_bootstraps()
    choices = new_command._gui_bootstrap_choices(bootstraps)
    other_index = list(choices.keys()).index(new_command.OTHER_FRAMEWORKS) + 1

    new_command.console.values = [
        str(other_index),  # Other frameworks (main menu)
        "1",  # Select first community option
    ]

    with pytest.raises(briefcase.commands.new.BriefcaseCommandError):
        new_command.create_bootstrap(
            context={
                "app_name": "myapplication",
                "author": "Grace Hopper",
            },
            project_overrides={},
        )

    out = capsys.readouterr().out
    assert "python -m pip install" in out


def test_other_frameworks_hides_installed_plugins(new_command, capsys, monkeypatch):
    """Installed community bootstraps are not shown in the submenu."""
    from briefcase.bootstraps import BaseGuiBootstrap

    class DummyBootstrap(BaseGuiBootstrap):
        fields = ()

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstraps",
        lambda: {
            "Toga": DummyBootstrap,
            "PySide6": DummyBootstrap,
            "Pygame": DummyBootstrap,
            "Console": DummyBootstrap,
            "PursuedPyBear": DummyBootstrap,  # installed community bootstrap
            "None": DummyBootstrap,
        },
    )

    new_command.console.values = [
        "6",  # Other frameworks (main menu)
        "1",  # pick whatever is now first in submenu (likely pygame-ce)
    ]

    with pytest.raises(briefcase.commands.new.BriefcaseCommandError):
        new_command.create_bootstrap(
            context={"app_name": "myapplication", "author": "Grace Hopper"},
            project_overrides={},
        )

    out = capsys.readouterr().out

    _, submenu = out.split("-- Community GUI Framework", 1)

    assert "1) pygame-ce" in submenu
    assert "PursuedPyBear" not in submenu


def test_question_sequence_with_overrides(
    new_command,
    mock_builtin_bootstraps,
    monkeypatch,
):
    """The answer to the bootstrap question can be overridden."""

    # Prime answers for none of the questions.
    new_command.console.values = []

    class GuiBootstrap:
        fields: Collection[str] = []

        def __init__(self, console, context):
            self.context = context.copy()

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstraps",
        MagicMock(
            return_value={
                **mock_builtin_bootstraps,
                "Custom GUI": GuiBootstrap,
            },
        ),
    )

    bootstrap = new_command.create_bootstrap(
        context={
            "app_name": "myapplication",
            "author": "Grace Hopper",
        },
        project_overrides={
            "bootstrap": "Custom GUI",
        },
    )

    assert isinstance(bootstrap, GuiBootstrap)
    assert bootstrap.context == {
        "app_name": "myapplication",
        "author": "Grace Hopper",
    }


def test_question_sequence_with_bad_bootstrap_override(
    new_command,
    mock_builtin_bootstraps,
    monkeypatch,
):
    """A bad override for the bootstrap uses user input instead."""

    # Prime a bad answer for the bootstrap question
    new_command.console.values = [
        "7",  # None
    ]

    class GuiBootstrap:
        # if this custom bootstrap is chosen, the lack of
        # requires() would cause an error
        fields: Collection[str] = ["requires"]

        def __init__(self, console, context):
            pass

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstraps",
        MagicMock(
            return_value={
                **mock_builtin_bootstraps,
                "Custom GUI": GuiBootstrap,
            },
        ),
    )

    bootstrap = new_command.create_bootstrap(
        context={
            "app_name": "myapplication",
            "author": "Grace Hopper",
        },
        project_overrides={
            "bootstrap": "BAD i don't exist GUI",
        },
    )

    assert isinstance(bootstrap, BaseGuiBootstrap)
    assert bootstrap.context == {
        "app_name": "myapplication",
        "author": "Grace Hopper",
    }


def test_question_sequence_with_no_user_input(new_command):
    """If no user input is provided, all user inputs are taken as default."""

    new_command.console.input_enabled = False

    bootstrap = new_command.create_bootstrap(
        context={
            "app_name": "myapplication",
            "author": "Grace Hopper",
        },
        project_overrides={},
    )

    assert isinstance(bootstrap, TogaGuiBootstrap)
    assert bootstrap.context == {
        "app_name": "myapplication",
        "author": "Grace Hopper",
    }
