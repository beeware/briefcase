import importlib
from types import MethodType, SimpleNamespace

import pytest


def test_select_target_device_success_path(monkeypatch, tmp_path):
    xcode = importlib.import_module("briefcase.platforms.iOS.xcode")

    # minimal console & tools
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

    console = Console()
    tools = SimpleNamespace(host_os="Darwin", console=console)
    cmd = xcode.iOSXcodeRunCommand(console=console, tools=tools)

    seen = {}

    # Force a successful selection (covers the "try: ..." non-exception branch)
    def fake_select(self, udid):
        seen["udid_arg"] = udid
        return ("UDID-OK", "17.5", "iPhone 14")

    cmd.select_target_device = MethodType(fake_select, cmd)

    # Stop the run right after selection to avoid heavy logic
    cmd.get_device_state = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("stop"))
    cmd.binary_path = lambda _app: tmp_path / "Demo.app"

    app = SimpleNamespace(
        app_name="Demo",
        formal_name="Demo",
        bundle_identifier="com.example.demo",
        test_mode=True,
        iOS={"device": None},
    )

    with pytest.raises(RuntimeError) as exc:
        # Pass a concrete UDID so we also exercise the path where `udid` is not None
        cmd.run_app(app, passthrough=[], udid="SOME-UDID")
    assert str(exc.value) == "stop"
    assert seen["udid_arg"] == "SOME-UDID"
