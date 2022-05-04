import subprocess

import pytest
from unittest import mock

from briefcase.console import Log
from briefcase.integrations.subprocess import PopenStreamingError


@pytest.fixture
def popen_process():
    process = mock.MagicMock()

    process.stdout.readline.side_effect = ["output line 1\n", "\n", "output line 3\n", ""]
    process.poll.side_effect = [None, None, None, -3]

    return process


def test_output(mock_sub, popen_process, capsys):
    "Readline output is printed"
    mock_sub.stream_output(popen_process)
    assert capsys.readouterr().out == "output line 1\n\noutput line 3\n"


def test_output_debug(mock_sub, popen_process, capsys):
    "Readline output is printed"
    mock_sub.command.logger = Log(verbosity=2)

    mock_sub.stream_output(popen_process)
    assert capsys.readouterr().out == "output line 1\n\noutput line 3\n"


def test_output_deep_debug(mock_sub, popen_process, capsys):
    "Readline output is printed with debug return code"
    mock_sub.command.logger = Log(verbosity=3)

    mock_sub.stream_output(popen_process)
    assert capsys.readouterr().out == "output line 1\n\noutput line 3\n>>> Return code: -3\n"


def test_streaming_error(mock_sub, popen_process, capsys):
    "Raise PopenStreamingError for any Exceptions from interacting with the OS process"
    popen_process.stdout.readline.side_effect = Exception("error reason")

    with pytest.raises(PopenStreamingError, match=r"Exception\(\'error reason\'\)"):
        mock_sub.stream_output(popen_process)
    assert capsys.readouterr().out == ""


def test_keyboard_interrupt(mock_sub, popen_process):
    "Process is terminated if user sends CTRL+C"
    popen_process.stdout.readline.side_effect = KeyboardInterrupt()
    popen_process.wait.side_effect = subprocess.TimeoutExpired(cmd="ls", timeout=3)

    mock_sub.stream_output(popen_process)

    popen_process.terminate.assert_called()
    popen_process.wait.assert_called()
    popen_process.kill.assert_called()


def test_process_exit_with_queued_output(mock_sub, popen_process, capsys):
    "All output is printed despite the process exiting early"
    popen_process.poll.side_effect = [None, -3, -3, -3]

    mock_sub.stream_output(popen_process)
    assert capsys.readouterr().out == "output line 1\n\noutput line 3\n"
