import subprocess
from unittest.mock import Mock

from briefcase.integrations.android_sdk import ADB


def test_pidof_succeed(mock_tools):
    adb = ADB(mock_tools, "exampleDevice")
    adb.run = Mock(return_value="5678\n")
    assert adb.pidof("com.example") == "5678"
    adb.run.assert_called_once_with("shell", "pidof", "-s", "com.example")


def test_pidof_fail_exit_0(mock_tools):
    adb = ADB(mock_tools, "exampleDevice")
    adb.run = Mock(return_value="")
    assert adb.pidof("com.example") is None


def test_pidof_fail_exit_1(mock_tools):
    adb = ADB(mock_tools, "exampleDevice")
    adb.run = Mock(side_effect=subprocess.CalledProcessError(1, "adb shell"))
    assert adb.pidof("com.example") is None
