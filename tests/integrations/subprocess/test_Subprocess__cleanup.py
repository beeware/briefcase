import subprocess
from unittest import mock


def test_clean_termination(mock_sub, capsys):
    """A popen process can be cleanly terminated."""
    process = mock.MagicMock(spec_set=subprocess.Popen)

    mock_sub.cleanup("testing process", process)

    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=3)
    process.kill.assert_not_called()

    # No log messages for a clean exit
    assert capsys.readouterr().out == ""


def test_dirty_termination(mock_sub, capsys):
    """If terminate doesn't stop the process, it will be forcibly killed."""
    process = mock.MagicMock(spec_set=subprocess.Popen)
    process.wait.side_effect = subprocess.TimeoutExpired(cmd="ls", timeout=3)

    mock_sub.cleanup("testing process", process)

    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=3)
    process.kill.assert_called_once_with()

    # Log contains a contextual message.
    assert capsys.readouterr().out == "Forcibly killing testing process...\n"
