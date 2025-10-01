import importlib
import uuid

import pytest


def test_select_target_device_udid_not_found():
    mod = importlib.import_module("briefcase.platforms.iOS.xcode")

    class Tools:
        host_os = "Darwin"  # required by integrations' verify_host()

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

        def selection_question(self, *a, **k):
            return None

    cmd = mod.iOSXcodeRunCommand(console=Console(), tools=Tools())

    # Simulators exist but *not* the UDID we pass
    cmd.get_simulators = lambda tools, platform: {
        "iOS 17.5": {"AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE": "iPhone 14"}
    }

    missing_udid = str(uuid.uuid4()).upper()
    with pytest.raises(mod.InvalidDeviceError) as exc:
        cmd.select_target_device(missing_udid)
    assert "device UDID" in str(exc.value)
