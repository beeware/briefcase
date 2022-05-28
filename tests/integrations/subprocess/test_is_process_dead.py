import pytest

from briefcase.integrations.subprocess import is_process_dead


@pytest.mark.parametrize("is_pid_exists, is_dead", [(True, False), (False, True)])
def test_is_process_dead(is_pid_exists, is_dead, monkeypatch):
    """Returns inverse of whether PID exists."""
    monkeypatch.setattr("psutil.pid_exists", lambda pid: is_pid_exists)
    assert is_process_dead(100) is is_dead
