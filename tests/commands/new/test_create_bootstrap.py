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
from briefcase.exceptions import BriefcaseWarning


class FakeEntryPoint:
    def __init__(self, obj):
        self._obj = obj

    def load(self):
        return self._obj


@pytest.fixture
def mock_builtin_bootstraps():
    return {
        "None": EmptyBootstrap,
        "Toga": TogaGuiBootstrap,
        "Console": ConsoleBootstrap,
        "PySide6": PySide6GuiBootstrap,
        "Pygame": PygameGuiBootstrap,
    }


@pytest.fixture
def patched_entry_points(mock_builtin_bootstraps, monkeypatch):
    eps = {name: FakeEntryPoint(cls) for name, cls in mock_builtin_bootstraps.items()}
    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstrap_entry_points",
        lambda: eps,
    )
    return eps


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

    eps = {
        **{name: FakeEntryPoint(cls) for name, cls in mock_builtin_bootstraps.items()},
        "Custom GUI": FakeEntryPoint(GuiBootstrap),
    }

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstrap_entry_points",
        MagicMock(return_value=eps),
    )

    app_context = {
        "app_name": "myapplication",
        "author": "Grace Hopper",
    }

    # override selects Custom GUI without requiring user input
    bootstrap_class = new_command.select_bootstrap(
        project_overrides={"bootstrap": "Custom GUI"}
    )

    bootstrap = bootstrap_class(console=new_command.console, context=app_context)

    assert isinstance(bootstrap, GuiBootstrap)
    assert passed_context == app_context


def test_question_sequence_toga(new_command):
    """The Toga bootstrap can be selected."""

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    bootstrap_class = new_command.select_bootstrap(
        project_overrides={"bootstrap": "Toga"}
    )
    bootstrap = bootstrap_class(console=new_command.console, context=context)

    assert isinstance(bootstrap, TogaGuiBootstrap)
    assert bootstrap.context == context


def test_question_sequence_console(new_command):
    """A console bootstrap can be constructed."""

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    bootstrap_class = new_command.select_bootstrap(
        project_overrides={"bootstrap": "Console"}
    )
    bootstrap = bootstrap_class(console=new_command.console, context=context)

    assert isinstance(bootstrap, ConsoleBootstrap)
    assert bootstrap.context == context


def test_question_sequence_pyside6(new_command):
    """A PySide6 bootstrap can be created."""

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    bootstrap_class = new_command.select_bootstrap(
        project_overrides={"bootstrap": "PySide6"}
    )
    bootstrap = bootstrap_class(console=new_command.console, context=context)

    assert isinstance(bootstrap, PySide6GuiBootstrap)
    assert bootstrap.context == context


def test_question_sequence_pygame(new_command):
    """A Pygame bootstrap can be constructed."""

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    bootstrap_class = new_command.select_bootstrap(
        project_overrides={"bootstrap": "Pygame"}
    )
    bootstrap = bootstrap_class(console=new_command.console, context=context)

    assert isinstance(bootstrap, PygameGuiBootstrap)
    assert bootstrap.context == context


def test_question_sequence_none(new_command):
    """If no bootstrap is selected, the empty bootstrap is used."""

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    bootstrap_class = new_command.select_bootstrap(
        project_overrides={"bootstrap": "None"}
    )
    bootstrap = bootstrap_class(console=new_command.console, context=context)

    assert isinstance(bootstrap, EmptyBootstrap)
    assert bootstrap.context == context


def test_question_sequence_other_frameworks_aborts(
    new_command,
    patched_entry_points,
    capsys,
    monkeypatch,
):
    """Selecting 'Other frameworks…' shows guidance and aborts cleanly."""
    monkeypatch.setattr(
        type(new_command),
        "KNOWN_COMMUNITY_PLUGINS",
        [
            {
                "package": "fake-framework",
                "display_name": "Fake Framework",
                "description": "A fake community framework.",
            }
        ],
        raising=False,
    )
    monkeypatch.setattr(briefcase.commands.new, "is_package_installed", lambda _: False)

    choices = new_command._gui_bootstrap_choices(list(patched_entry_points.keys()))
    other_index = list(choices.keys()).index(new_command.OTHER_FRAMEWORKS) + 1

    new_command.console.values = [str(other_index), "1"]

    with pytest.raises(BriefcaseWarning) as excinfo:
        new_command.select_bootstrap(project_overrides={})

    out = capsys.readouterr().out
    assert "Community GUI Framework" in out
    assert "Fake Framework" in out

    # Guidance text is in the exception message.
    msg = str(excinfo.value)
    assert "python -m pip install fake-framework" in msg
    assert "then re-run `briefcase new`" in msg


def test_other_frameworks_hides_installed_plugins(
    new_command,
    patched_entry_points,
    capsys,
    monkeypatch,
):
    """Installed community plugins are not shown in the submenu."""
    monkeypatch.setattr(
        type(new_command),
        "KNOWN_COMMUNITY_PLUGINS",
        [
            {"package": "toga-positron", "display_name": "Positron"},
            {"package": "pygame-ce", "display_name": "Pygame-ce"},
        ],
        raising=False,
    )

    monkeypatch.setattr(
        briefcase.commands.new,
        "is_package_installed",
        lambda package: package == "toga-positron",
    )

    choices = new_command._gui_bootstrap_choices(list(patched_entry_points.keys()))
    other_index = list(choices.keys()).index(new_command.OTHER_FRAMEWORKS) + 1

    new_command.console.values = [str(other_index), "1"]

    with pytest.raises(BriefcaseWarning):
        new_command.select_bootstrap(project_overrides={})

    out = capsys.readouterr().out
    assert "Community GUI Framework" in out
    assert "Pygame-ce" in out
    assert "Positron" not in out


def test_other_frameworks_no_available_plugins(
    new_command,
    patched_entry_points,
    capsys,
    monkeypatch,
):
    """If no community GUI plugins are available, show guidance and abort."""
    monkeypatch.setattr(
        type(new_command),
        "KNOWN_COMMUNITY_PLUGINS",
        [
            {"package": "toga-positron", "display_name": "Positron"},
            {"package": "pygame-ce", "display_name": "Pygame-ce"},
        ],
        raising=False,
    )
    monkeypatch.setattr(briefcase.commands.new, "is_package_installed", lambda _: True)

    choices = new_command._gui_bootstrap_choices(list(patched_entry_points.keys()))
    other_index = list(choices.keys()).index(new_command.OTHER_FRAMEWORKS) + 1

    new_command.console.values = [str(other_index)]

    with pytest.raises(BriefcaseWarning) as excinfo:
        new_command.select_bootstrap(project_overrides={})

    out = capsys.readouterr().out

    assert "-- GUI Framework" in out
    assert "Other frameworks (select to see options)" in out

    msg = str(excinfo.value)
    assert "GUI frameworks listed here are provided by third-party plugins" in msg
    assert (
        "No additional community GUI bootstraps are currently available to install."
        in msg
    )
    assert "Browse options at https://beeware.org/bee/briefcase-bootstraps" in msg
    assert "Re-run `briefcase new`" in msg


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

    eps = {
        **{name: FakeEntryPoint(cls) for name, cls in mock_builtin_bootstraps.items()},
        "Custom GUI": FakeEntryPoint(GuiBootstrap),
    }

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstrap_entry_points",
        MagicMock(return_value=eps),
    )

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    bootstrap_class = new_command.select_bootstrap(
        project_overrides={"bootstrap": "Custom GUI"}
    )
    bootstrap = bootstrap_class(console=new_command.console, context=context)

    assert isinstance(bootstrap, GuiBootstrap)
    assert bootstrap.context == context


def test_question_sequence_with_bad_bootstrap_override(
    new_command,
    mock_builtin_bootstraps,
    monkeypatch,
):
    """A bad override for the bootstrap uses user input instead."""

    class GuiBootstrap:
        # If this custom bootstrap is chosen, the lack of requires() would cause an error
        fields: Collection[str] = ["requires"]

        def __init__(self, console, context):
            pass

    eps = {
        **{name: FakeEntryPoint(cls) for name, cls in mock_builtin_bootstraps.items()},
        "Custom GUI": FakeEntryPoint(GuiBootstrap),
    }

    monkeypatch.setattr(
        briefcase.commands.new,
        "get_gui_bootstrap_entry_points",
        MagicMock(return_value=eps),
    )

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    # Simulate user selecting Toga from the menu after bad override.
    choices = new_command._gui_bootstrap_choices(list(eps.keys()))
    toga_index = list(choices.keys()).index("Toga") + 1
    new_command.console.values = [str(toga_index)]

    bootstrap_class = new_command.select_bootstrap(
        project_overrides={"bootstrap": "BAD i don't exist GUI"}
    )
    bootstrap = bootstrap_class(console=new_command.console, context=context)

    assert isinstance(bootstrap, TogaGuiBootstrap)
    assert bootstrap.context == context


def test_question_sequence_with_no_user_input(new_command):
    """If no user input is provided, all user inputs are taken as default."""

    new_command.console.input_enabled = False

    context = {"app_name": "myapplication", "author": "Grace Hopper"}

    bootstrap_class = new_command.select_bootstrap(project_overrides={})
    bootstrap = bootstrap_class(console=new_command.console, context=context)

    assert isinstance(bootstrap, TogaGuiBootstrap)
    assert bootstrap.context == context
