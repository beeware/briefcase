import importlib
import types

import pytest

gradle = importlib.import_module("briefcase.platforms.android.gradle")


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


class Tools:
    host_os = "Windows"  # satisfies integrations' verify_host()

    class subprocess:
        pass


def _make_cmd():
    return gradle.GradleRunCommand(console=Console(), tools=Tools())


def test_uses_android_dict_device_and_strips(tmp_path):
    """device_or_avd is None; take app.android['device'] and .strip() it."""
    cmd = _make_cmd()
    seen = {}

    # select_target_device should receive the stripped value
    def fake_select(device_or_avd):
        seen["arg"] = device_or_avd
        raise RuntimeError("stop")  # escape early; not caught by run_app

    cmd.tools.android_sdk = types.SimpleNamespace(
        env={}, select_target_device=fake_select
    )

    app = types.SimpleNamespace(
        app_name="Demo",
        formal_name="Demo",
        bundle_identifier="com.example.demo",
        package_name="com.example",
        module_name="demo",
        test_mode=True,
        android={"device": "   @Pixel_5   "},  # dict path
    )

    with pytest.raises(RuntimeError):
        cmd.run_app(app, passthrough=[], device_or_avd=None)

    assert seen["arg"] == "@Pixel_5"  # <- proves strip & dict branch


def test_uses_android_object_device(tmp_path):
    """device_or_avd is None; take app.android.device (object attr path)."""
    cmd = _make_cmd()
    seen = {}

    def fake_select(device_or_avd):
        seen["arg"] = device_or_avd
        raise RuntimeError("stop")

    cmd.tools.android_sdk = types.SimpleNamespace(
        env={}, select_target_device=fake_select
    )

    app = types.SimpleNamespace(
        app_name="Demo",
        formal_name="Demo",
        bundle_identifier="com.example.demo",
        package_name="com.example",
        module_name="demo",
        test_mode=True,
        android=types.SimpleNamespace(device="@Pixel_6"),  # object path
    )

    with pytest.raises(RuntimeError):
        cmd.run_app(app, passthrough=[], device_or_avd=None)

    assert seen["arg"] == "@Pixel_6"


def test_invalid_device_is_wrapped_to_briefcase_error():
    """InvalidDeviceError from select_target_device becomes BriefcaseCommandError."""
    cmd = _make_cmd()

    def raise_invalid(device_or_avd):
        # Pass both args expected by InvalidDeviceError: (tools, device)
        raise gradle.InvalidDeviceError(cmd.tools, "@Nope")

    cmd.tools.android_sdk = types.SimpleNamespace(
        env={}, select_target_device=raise_invalid
    )

    app = types.SimpleNamespace(
        app_name="Demo",
        formal_name="Demo",
        bundle_identifier="com.example.demo",
        package_name="com.example",
        module_name="demo",
        test_mode=True,
        android={"device": "@Nope"},  # used since device_or_avd=None
    )

    with pytest.raises(gradle.BriefcaseCommandError) as exc:
        cmd.run_app(app, passthrough=[], device_or_avd=None)

    assert "Unable to find device or AVD '@Nope'." in str(exc.value)
