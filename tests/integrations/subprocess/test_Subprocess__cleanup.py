import subprocess
from unittest import mock


def test_clean_termination(mock_sub, capsys):
    """A popen process that has already exited is not reported as terminated."""
    process = mock.MagicMock(spec_set=subprocess.Popen)
    # The process has already exited.
    process.poll.return_value = 0

    mock_sub.cleanup("testing process", process)

    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=3)
    process.kill.assert_not_called()

    # No log messages for a clean exit
    assert capsys.readouterr().out == ""


def test_dirty_termination(mock_sub, capsys):
    """If terminate doesn't stop the process, it will be forcibly killed."""
    process = mock.MagicMock(spec_set=subprocess.Popen)
    # The process has already exited, but won't be reaped.
    process.poll.return_value = 0
    process.wait.side_effect = subprocess.TimeoutExpired(cmd="ls", timeout=3)

    mock_sub.cleanup("testing process", process)

    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=3)
    process.kill.assert_called_once_with()

    # Log contains a contextual message.
    assert capsys.readouterr().out == "Forcibly killing testing process...\n"


def test_termination_of_live_process(mock_sub, capsys):
    """If the process is still running at cleanup, that fact is reported."""
    process = mock.MagicMock(spec_set=subprocess.Popen)
    # The process is still running.
    process.poll.return_value = None

    mock_sub.cleanup("testing process", process)

    process.terminate.assert_called_once()

    # The termination of a live process is reported, since on Windows this is
    # indistinguishable from the process exiting with status 1.
    output = capsys.readouterr().out
    assert "testing process was still running at cleanup" in output
    assert "exit status of 1" in output
