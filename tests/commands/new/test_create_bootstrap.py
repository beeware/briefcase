from collections.abc import Collection
from unittest.mock import MagicMock

import pytest

import briefcase.commands.new
from briefcase.bootstraps import (
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

    app_context = {
        "app_name": "myapplication",
        "author": "Grace Hopper",
    }

    selected, bootstraps = new_command.select_bootstrap(
        project_overrides={"bootstrap": "Custom GUI"}
    )
    bootstrap = new_command._instantiate_bootstrap(selected, bootstraps, app_context)

    assert isinstance(bootstrap, GuiBootstrap)
    assert passed_context == app_context


def test_question_sequence_toga(new_command):
    """The Toga bootstrap can be selected."""

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    selected, bootstraps = new_command.select_bootstrap(
        project_overrides={"bootstrap": "Toga"}
    )
    bootstrap = new_command._instantiate_bootstrap(selected, bootstraps, context)

    assert isinstance(bootstrap, TogaGuiBootstrap)
    assert bootstrap.context == context


def test_question_sequence_console(new_command):
    """A console bootstrap can be constructed."""

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    selected, bootstraps = new_command.select_bootstrap(
        project_overrides={"bootstrap": "Console"}
    )
    bootstrap = new_command._instantiate_bootstrap(selected, bootstraps, context)

    assert isinstance(bootstrap, ConsoleBootstrap)
    assert bootstrap.context == context


def test_question_sequence_pyside6(new_command):
    """A PySide6 bootstrap can be created."""

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    selected, bootstraps = new_command.select_bootstrap(
        project_overrides={"bootstrap": "PySide6"}
    )
    bootstrap = new_command._instantiate_bootstrap(selected, bootstraps, context)

    assert isinstance(bootstrap, PySide6GuiBootstrap)
    assert bootstrap.context == context


def test_question_sequence_pygame(new_command):
    """A Pygame bootstrap can be constructed."""

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    selected, bootstraps = new_command.select_bootstrap(
        project_overrides={"bootstrap": "Pygame"}
    )
    bootstrap = new_command._instantiate_bootstrap(selected, bootstraps, context)

    assert isinstance(bootstrap, PygameGuiBootstrap)
    assert bootstrap.context == context


def test_question_sequence_none(new_command):
    """If no bootstrap is selected, the empty bootstrap is used."""

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    selected, bootstraps = new_command.select_bootstrap(
        project_overrides={"bootstrap": "None"}
    )
    bootstrap = new_command._instantiate_bootstrap(selected, bootstraps, context)

    assert isinstance(bootstrap, EmptyBootstrap)
    assert bootstrap.context == context


def test_question_sequence_other_frameworks_aborts(
    new_command,
    mock_builtin_bootstraps,
    capsys,
    monkeypatch,
):
    """Selecting 'Other frameworks…' shows guidance and aborts cleanly."""
    monkeypatch.setattr(
        type(new_command),
        "KNOWN_COMMUNITY_BOOTSTRAPS",
        {
            "fake-framework": {
                "entry_point": "fake_framework",
                "display_name": "Fake Framework",
                "description": "A fake community framework.",
            }
        },
        raising=False,
    )
    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstraps",
        MagicMock(return_value=mock_builtin_bootstraps),
    )

    choices = new_command._gui_bootstrap_choices(mock_builtin_bootstraps)
    other_index = list(choices.keys()).index(new_command.OTHER_FRAMEWORKS) + 1

    new_command.console.values = [str(other_index), "1"]

    with pytest.raises(SystemExit) as excinfo:
        new_command.select_bootstrap(project_overrides={})

    assert excinfo.value.code == 0

    out = capsys.readouterr().out
    assert "Community GUI Framework" in out
    assert "Fake Framework" in out
    assert "python -m pip install fake-framework" in out
    assert "then re-run `briefcase new`" in out


def test_other_frameworks_hides_installed_plugins(
    new_command,
    mock_builtin_bootstraps,
    capsys,
    monkeypatch,
):
    """Installed community bootstraps are not shown in the submenu."""
    monkeypatch.setattr(
        type(new_command),
        "KNOWN_COMMUNITY_BOOTSTRAPS",
        {
            "toga-positron": {
                "entry_point": "fake_positron",
                "display_name": "Positron",
                "description": "A Toga base for apps whose GUI "
                "is provided by a web view.",
            },
            "pygame-ce": {
                "entry_point": "pygame_ce",
                "display_name": "Pygame-ce",
                "description": "Community edition fork of pygame.",
            },
        },
        raising=False,
    )

    # Simulate toga-positron being installed by adding its entry point to bootstraps
    installed_bootstraps = {
        **mock_builtin_bootstraps,
        "fake_positron": None,
    }

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstraps",
        MagicMock(return_value=installed_bootstraps),
    )

    choices = new_command._gui_bootstrap_choices(installed_bootstraps)
    other_index = list(choices.keys()).index(new_command.OTHER_FRAMEWORKS) + 1

    new_command.console.values = [str(other_index), "1"]

    with pytest.raises(SystemExit):
        new_command.select_bootstrap(project_overrides={})

    out = capsys.readouterr().out
    assert "Community GUI Framework" in out
    assert "Pygame-ce" in out
    assert "Positron" not in out


def test_other_frameworks_no_available_plugins(
    new_command,
    mock_builtin_bootstraps,
    capsys,
    monkeypatch,
):
    """If no community GUI bootstraps are available, show guidance and abort."""
    monkeypatch.setattr(
        type(new_command),
        "KNOWN_COMMUNITY_BOOTSTRAPS",
        {
            "toga-positron": {
                "entry_point": "Toga Positron (Django server)",
                "display_name": "Positron",
                "description": "A Toga base for apps whose GUI "
                "is provided by a web view.",
            },
            "pygame-ce": {
                "entry_point": "pygame_ce",
                "display_name": "Pygame-ce",
                "description": "Community edition fork of pygame.",
            },
        },
        raising=False,
    )

    # Simulate all community bootstraps being installed
    installed_bootstraps = {
        **mock_builtin_bootstraps,
        "Toga Positron (Django server)": None,
        "pygame_ce": None,
    }

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstraps",
        MagicMock(return_value=installed_bootstraps),
    )

    choices = new_command._gui_bootstrap_choices(installed_bootstraps)
    other_index = list(choices.keys()).index(new_command.OTHER_FRAMEWORKS) + 1

    new_command.console.values = [str(other_index)]

    with pytest.raises(SystemExit) as excinfo:
        new_command.select_bootstrap(project_overrides={})

    assert excinfo.value.code == 0

    out = capsys.readouterr().out
    assert "-- GUI Framework" in out
    assert "Other frameworks (select to see options)" in out
    assert "GUI frameworks listed here are provided by third-party plugins" in out
    assert (
        "No additional community GUI bootstraps are currently available to install."
        in out
    )
    assert "Browse options at https://beeware.org/bee/briefcase-bootstraps" in out
    assert "Re-run `briefcase new`" in out


def test_question_sequence_with_overrides(
    new_command,
    mock_builtin_bootstraps,
    monkeypatch,
):
    """The answer to the bootstrap question can be overridden."""

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

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    selected, bootstraps = new_command.select_bootstrap(
        project_overrides={"bootstrap": "Custom GUI"}
    )
    bootstrap = new_command._instantiate_bootstrap(selected, bootstraps, context)

    assert isinstance(bootstrap, GuiBootstrap)
    assert bootstrap.context == context


def test_question_sequence_with_bad_bootstrap_override(
    new_command,
    mock_builtin_bootstraps,
    monkeypatch,
):
    """A bad override for the bootstrap uses user input instead."""

    class GuiBootstrap:
        # If this custom bootstrap is chosen, the lack of requires()
        # would cause an error
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

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    # Simulate user selecting Toga from the menu after bad override.
    choices = new_command._gui_bootstrap_choices(
        {
            **mock_builtin_bootstraps,
            "Custom GUI": GuiBootstrap,
        }
    )
    toga_index = list(choices.keys()).index("Toga") + 1
    new_command.console.values = [str(toga_index)]

    selected, bootstraps = new_command.select_bootstrap(
        project_overrides={"bootstrap": "BAD i don't exist GUI"}
    )
    bootstrap = new_command._instantiate_bootstrap(selected, bootstraps, context)

    assert isinstance(bootstrap, TogaGuiBootstrap)
    assert bootstrap.context == context


def test_question_sequence_with_no_user_input(new_command):
    """If no user input is provided, all user inputs are taken as default."""

    new_command.console.input_enabled = False

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    selected, bootstraps = new_command.select_bootstrap(project_overrides={})
    bootstrap = new_command._instantiate_bootstrap(selected, bootstraps, context)

    assert isinstance(bootstrap, TogaGuiBootstrap)
    assert bootstrap.context == context
