from unittest.mock import MagicMock

from briefcase.integrations.android_sdk import ADB


def test_install_apk(mock_sdk, capsys):
    "Invoking `install_apk()` calls `run()` with the appropriate parameters."
    # Mock out the run command on an adb instance
    adb = ADB(mock_sdk, "exampleDevice")
    adb.run = MagicMock(return_value=b"example normal adb output")

    # Invoke install
    adb.install_apk("example.apk")

    # Validate call parameters.
    adb.run.assert_called_once_with("install", "example.apk")

    # Validate that the normal output of the command was not printed (since there
    # was no error).
    assert "normal adb output" not in capsys.readouterr()
