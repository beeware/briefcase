import importlib
from types import MethodType, SimpleNamespace

import pytest

xcode = importlib.import_module("briefcase.platforms.iOS.xcode")


class Console:
    def info(self, *a, **k):
        pass

    def error(self, *a, **k):
        pass

    def wait_bar(self, *a, **k):
        class Bar:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                pass

            def update(self):
                pass

        return Bar()


def _cmd():
    console = Console()
    tools = SimpleNamespace(host_os="Darwin", console=console)
    return xcode.iOSXcodeRunCommand(console=console, tools=tools)


def test_udid_from_ios_dict_blank_becomes_none(tmp_path):
    """Udid is None, app.iOS is dict with blank 'device' -> None after strip (line
    538)."""
    cmd = _cmd()
    seen = {}

    def fake_select(self, udid):
        seen["udid"] = udid
        raise RuntimeError("stop")  # escape after preselection

    cmd.select_target_device = MethodType(fake_select, cmd)
    app = SimpleNamespace(
        app_name="Demo",
        formal_name="Demo",
        bundle_identifier="com.example.demo",
        test_mode=True,
        iOS={"device": "   "},  # -> None
    )

    with pytest.raises(RuntimeError):
        cmd.run_app(app, passthrough=[], udid=None)

    assert seen["udid"] is None


def test_udid_from_ios_object_is_stripped(tmp_path):
    """Udid is None, app.iOS is an object; code reads app.device and strips it."""
    cmd = _cmd()
    seen = {}

    def fake_select(self, udid):
        seen["udid"] = udid
        raise RuntimeError("stop")

    cmd.select_target_device = MethodType(fake_select, cmd)

    app = SimpleNamespace(
        app_name="Demo",
        formal_name="Demo",
        bundle_identifier="com.example.demo",
        test_mode=True,
        iOS=SimpleNamespace(),
        device="  UDID-XYZ  ",
    )

    with pytest.raises(RuntimeError):
        cmd.run_app(app, passthrough=[], udid=None)

    assert seen["udid"] == "UDID-XYZ"


def test_input_disabled_maps_to_briefcase_error(tmp_path):
    """InputDisabled during selection -> BriefcaseCommandError (lines 541–542)."""
    cmd = _cmd()

    def raise_input_disabled(self, udid):
        raise xcode.InputDisabled("no tty")

    cmd.select_target_device = MethodType(raise_input_disabled, cmd)
    app = SimpleNamespace(
        app_name="Demo",
        formal_name="Demo",
        bundle_identifier="com.example.demo",
        test_mode=True,
        iOS=SimpleNamespace(device="UDID-ABC"),
    )

    with pytest.raises(xcode.BriefcaseCommandError) as exc:
        cmd.run_app(app, passthrough=[], udid=None)

    assert "Input has been disabled; can't select a device to target." in str(exc.value)
