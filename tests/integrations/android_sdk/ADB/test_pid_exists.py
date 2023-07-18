import subprocess
from unittest.mock import Mock


def test_pid_exists_succeed(adb):
    """adb.pid_exists() can be called on a process that exists."""
    adb.run = Mock(return_value="")

    assert adb.pid_exists("1234")
    adb.run.assert_called_once_with("shell", "test", "-e", "/proc/1234")


def test_pid_exists_quiet(adb):
    """adb.pid_exists() can be called in quiet mode on a process that exists."""
    adb.run = Mock(return_value="")

    assert adb.pid_exists("1234", quiet=True)
    adb.run.assert_called_once_with("shell", "test", "-e", "/proc/1234", quiet=True)


def test_pid_does_not_exist(adb):
    """If adb.pid_exists() returns a status code of 1, it is interpreted as the process
    not existing."""
    adb.run = Mock(side_effect=subprocess.CalledProcessError(returncode=1, cmd="test"))

    assert not adb.pid_exists("9999") is None
    adb.run.assert_called_once_with("shell", "test", "-e", "/proc/9999")
