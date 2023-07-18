import subprocess
from unittest.mock import Mock


def test_pidof_succeed(adb):
    """adb.pidof() can be called on a process that exists."""
    adb.run = Mock(return_value="5678\n")

    assert adb.pidof("com.example") == "5678"
    adb.run.assert_called_once_with("shell", "pidof", "-s", "com.example")


def test_pidof_quiet(adb):
    """adb.pidof() can be called in quiet mode on a process that exists."""
    adb.run = Mock(return_value="5678\n")

    assert adb.pidof("com.example", quiet=True) == "5678"
    adb.run.assert_called_once_with("shell", "pidof", "-s", "com.example", quiet=True)


def test_pidof_fail_exit_0(adb):
    """If adb.pidof() returns a PID of 0, it is interpreted as the process not
    existing."""
    adb.run = Mock(return_value="")

    assert adb.pidof("com.example") is None
    adb.run.assert_called_once_with("shell", "pidof", "-s", "com.example")


def test_pidof_fail_exit_1(adb):
    """If adb.pidof() fails, it is interpreted as the process not existing."""
    adb.run = Mock(side_effect=subprocess.CalledProcessError(1, "adb shell"))

    assert adb.pidof("com.example") is None
    adb.run.assert_called_once_with("shell", "pidof", "-s", "com.example")
