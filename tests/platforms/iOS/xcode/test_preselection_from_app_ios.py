# tests/platforms/iOS/xcode/test_preselection_from_app_ios.py
import importlib
import types

import pytest


def _make_cmd():
    mod = importlib.import_module("briefcase.platforms.iOS.xcode")

    class Tools:  # minimal to pass tool verification
        host_os = "Darwin"

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

    return mod, mod.iOSXcodeRunCommand(console=Console(), tools=Tools())


def test_preselect_udid_from_ios_dict_blank_becomes_none(tmp_path, monkeypatch):
    mod, cmd = _make_cmd()

    # Capture the UDID passed to select_target_device, then abort the run early.
    seen = {}

    def fake_select(self, udid):
        seen["udid"] = udid
        raise RuntimeError("stop here")

    cmd.select_target_device = types.MethodType(fake_select, cmd)

    app = types.SimpleNamespace(
        app_name="Demo",
        formal_name="Demo",
        bundle_identifier="com.example.demo",
        test_mode=True,
        iOS={"device": "   "},  # <- blank; should become None
    )
    cmd.binary_path = lambda _app: tmp_path / "Demo.app"

    with pytest.raises(RuntimeError):
        cmd.run_app(app, passthrough=[], udid=None)

    assert seen["udid"] is None


def test_preselect_udid_from_ios_dict_stripped_used(tmp_path):
    mod, cmd = _make_cmd()

    seen = {}

    def fake_select(self, udid):
        seen["udid"] = udid
        raise RuntimeError("stop here")

    cmd.select_target_device = types.MethodType(fake_select, cmd)

    app = types.SimpleNamespace(
        app_name="Demo",
        formal_name="Demo",
        bundle_identifier="com.example.demo",
        test_mode=True,
        iOS={"device": "  ABCD-1234  "},  # -> "ABCD-1234"
    )
    cmd.binary_path = lambda _app: tmp_path / "Demo.app"

    with pytest.raises(RuntimeError):
        cmd.run_app(app, passthrough=[], udid=None)

    assert seen["udid"] == "ABCD-1234"


def test_preselect_from_ios_object_and_input_disabled_maps_to_command_error(tmp_path):
    mod, cmd = _make_cmd()

    def raise_input_disabled(self, udid):
        raise mod.InputDisabled("no TTY")

    cmd.select_target_device = types.MethodType(raise_input_disabled, cmd)

    app = types.SimpleNamespace(
        app_name="Demo",
        formal_name="Demo",
        bundle_identifier="com.example.demo",
        test_mode=True,
        iOS=types.SimpleNamespace(device="  UDID-XYZ  "),  # attribute path
    )
    cmd.binary_path = lambda _app: tmp_path / "Demo.app"

    with pytest.raises(mod.BriefcaseCommandError) as exc:
        cmd.run_app(app, passthrough=[], udid=None)

    assert "Input has been disabled; can't select a device to target." in str(exc.value)
