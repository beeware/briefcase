from types import SimpleNamespace

import pytest

from briefcase.hooks import get_hooks
from briefcase.hooks.base import HOOK_STAGES, BaseHook, HookCommandAPI
from briefcase.hooks.commands import CommandsHook


class DummyHook(BaseHook):
    """A hook that records the stages it was dispatched to."""

    def __init__(self):
        self.calls = []

    @property
    def name(self):
        return "dummy"

    def pre_build(self, app, command, **options):
        self.calls.append(("pre_build", app, command, options))


def test_hook_command_api_is_runtime_checkable():
    """An object with the required attributes satisfies HookCommandAPI."""

    class Conforming:
        console = None
        tools = None
        base_path = None
        platform = "tester"
        output_format = "dummy"
        command = "build"

        def bundle_path(self, app):
            pass

        def build_path(self, app):
            pass

    assert isinstance(Conforming(), HookCommandAPI)


def test_hook_command_api_rejects_incomplete():
    """An object missing required attributes does not satisfy HookCommandAPI."""

    class Missing:
        console = None

    assert not isinstance(Missing(), HookCommandAPI)


def test_base_hook_requires_name():
    """A hook without a name cannot be instantiated."""

    class Nameless(BaseHook):
        pass

    with pytest.raises(TypeError):
        Nameless()


@pytest.mark.parametrize("stage", HOOK_STAGES)
def test_base_hook_stage_is_a_noop(stage):
    """Every stage method exists on the base class and does nothing."""
    hook = DummyHook()
    assert getattr(BaseHook, stage)(hook, app="app", command="command") is None


def test_invoke_dispatches_to_the_stage_method():
    """Dispatching a stage calls the method named by it, passing options through."""
    hook = DummyHook()

    hook.invoke("pre_build", "app", "command", extra=42)
    hook.invoke("post_build", "app", "command", extra=42)

    assert hook.calls == [("pre_build", "app", "command", {"extra": 42})]


def test_get_hooks_none_registered(monkeypatch):
    """With no entry points registered, no hooks are found."""
    monkeypatch.setattr("briefcase.hooks.entry_points", lambda group: [])
    assert get_hooks() == {}


def test_get_hooks_discovery(monkeypatch):
    """Registered entry points are loaded, keyed by entry point name."""
    monkeypatch.setattr(
        "briefcase.hooks.entry_points",
        lambda group: [SimpleNamespace(name="dummy", load=lambda: DummyHook)],
    )
    assert get_hooks() == {"dummy": DummyHook}


def test_get_hooks_builtin():
    """The built-in commands hook is registered through entry points."""
    assert get_hooks()["commands"] is CommandsHook
