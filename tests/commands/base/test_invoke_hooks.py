import pytest

from briefcase.exceptions import BriefcaseCommandError

from ...utils import FailingHook, RecordingHook, TrackingHook


class AlphaHook(RecordingHook):
    pass


class ZetaHook(RecordingHook):
    pass


def test_get_hooks_uses_entry_points(base_command, monkeypatch):
    """By default, hooks are discovered through entry points."""
    monkeypatch.setattr(
        "briefcase.commands.base.get_hooks",
        lambda: {"tracking": TrackingHook},
    )
    assert base_command._get_hooks() == {"tracking": TrackingHook}


def test_hooks_are_instantiated_once_in_name_order(base_command):
    """Hook classes are instantiated once per command, sorted by entry point name."""
    base_command._get_hooks = lambda: {"zeta": ZetaHook, "alpha": AlphaHook}

    hooks = base_command.hooks

    assert [type(hook) for hook in hooks] == [AlphaHook, ZetaHook]
    # A second access returns the same instances.
    assert base_command.hooks is hooks


def test_invoke_hooks_in_order_with_options(base_command, first_app_config):
    """Every hook is invoked for the stage, in order, with the command's options."""
    base_command._get_hooks = lambda: {"zeta": ZetaHook, "alpha": AlphaHook}

    base_command.invoke_hooks("pre_build", first_app_config, extra=42)

    assert base_command.actions == [
        ("AlphaHook", "pre_build", "first", {"extra": 42}),
        ("ZetaHook", "pre_build", "first", {"extra": 42}),
    ]


def test_invoke_hooks_without_hooks(base_command, first_app_config):
    """With no hooks registered, invoking a stage does nothing."""
    base_command._get_hooks = dict

    base_command.invoke_hooks("pre_build", first_app_config)

    assert base_command.hooks == []
    assert base_command.actions == []


def test_invoke_hooks_error_propagates(base_command, first_app_config):
    """An error raised by a hook stops the command."""
    base_command._get_hooks = lambda: {"failing": FailingHook, "alpha": AlphaHook}

    with pytest.raises(BriefcaseCommandError, match=r"The hook failed\."):
        base_command.invoke_hooks("pre_build", first_app_config)

    # alpha sorts first, so it ran; nothing after the failure ran.
    assert base_command.actions == [("AlphaHook", "pre_build", "first", {})]
