import importlib
from types import SimpleNamespace


def test_select_target_device_question_triggers_interactive(monkeypatch):
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

    console = Console()
    tools = SimpleNamespace(host_os="Darwin", console=console)
    cmd = xcode.iOSXcodeRunCommand(console=console, tools=tools)

    # Simulate user input: first an invalid entry, then the "?" to trigger
    simulators = {"iOS 17.5": {"UDID-1111-2222": "iPhone 14"}}
    monkeypatch.setattr(
        cmd, "get_simulators", lambda tools, platform: simulators, raising=True
    )

    udid, ios_version, device_name = cmd.select_target_device("  ?  ")
    assert udid == "UDID-1111-2222"
    assert ios_version == "17.5"  # prefix "iOS " is dropped by the code
    assert device_name == "iPhone 14"
