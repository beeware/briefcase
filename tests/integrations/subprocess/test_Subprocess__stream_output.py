import time
from io import StringIO
from threading import Event
from unittest import mock

import pytest

from briefcase.integrations import subprocess


@pytest.fixture()
def mock_sub(mock_sub):
    # also mock cleanup for stream output testing
    mock_sub.cleanup = mock.MagicMock()
    return mock_sub


def test_output(mock_sub, popen_process, capsys):
    """Process output is printed."""
    mock_sub.stream_output("testing", popen_process)

    # fmt: off
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on
    mock_sub.cleanup.assert_called_once_with("testing", popen_process)


def test_output_debug(mock_sub, popen_process, capsys):
    """Process output is printed; no debug output for only stream_output."""
    mock_sub.tools.logger.verbosity = 2

    mock_sub.stream_output("testing", popen_process)

    # fmt: off
    expected_output = (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output

    mock_sub.cleanup.assert_called_once_with("testing", popen_process)


def test_keyboard_interrupt(mock_sub, popen_process, capsys):
    """KeyboardInterrupt is suppressed if user sends CTRL+C and all output is
    printed."""

    send_ctrl_c = mock.MagicMock()
    send_ctrl_c.side_effect = [False, KeyboardInterrupt]

    with pytest.raises(KeyboardInterrupt):
        mock_sub.stream_output("testing", popen_process, stop_func=send_ctrl_c)

    assert (
        capsys.readouterr().out == "output line 1\n"
        "\n"
        "output line 3\n"
        "Stopping...\n"
    )
    mock_sub.cleanup.assert_called_once_with("testing", popen_process)


def test_process_exit_with_queued_output(mock_sub, popen_process, capsys):
    """All output is printed despite the process exiting early."""
    popen_process.poll.side_effect = [None, -3, -3, -3]

    mock_sub.stream_output("testing", popen_process)
    # fmt: off
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on
    mock_sub.cleanup.assert_called_once_with("testing", popen_process)


@pytest.mark.parametrize("stop_func_ret_val", (True, False))
def test_stop_func(mock_sub, popen_process, stop_func_ret_val, capsys):
    """All output is printed whether stop_func aborts streaming or not."""
    mock_sub.stream_output(
        "testing", popen_process, stop_func=lambda: stop_func_ret_val
    )
    # fmt: off
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on
    mock_sub.cleanup.assert_called_once_with("testing", popen_process)


def test_stuck_streamer(mock_sub, popen_process, monkeypatch, capsys):
    """Following a KeyboardInterrupt, output streaming returns even if the
    output streamer becomes stuck."""

    # Mock time.time() to return times that monotonically increase by 1s
    # every time it is invoked. This allows us to simulate the progress of
    # time much faster than the actual calls to time.sleep() would.
    mock_time = mock.MagicMock(side_effect=range(1000, 1005))
    monkeypatch.setattr(time, "time", mock_time)

    # Flag for the mock streamer to exit and prevent it
    # potentially printing in the middle of a later test.
    monkeypatched_streamer_should_exit = Event()

    def monkeypatched_blocked_streamer(*a, **kw):
        """Simulate a streamer that blocks longer than it will be waited on."""
        time.sleep(1)
        if monkeypatched_streamer_should_exit.is_set():
            return
        print("This should not be printed while waiting on the streamer to exit")

    monkeypatch.setattr(
        mock_sub,
        "_stream_output_thread",
        monkeypatched_blocked_streamer,
    )

    send_ctrl_c = mock.MagicMock()
    send_ctrl_c.side_effect = [False, KeyboardInterrupt]
    with pytest.raises(KeyboardInterrupt):
        mock_sub.stream_output("testing", popen_process, stop_func=send_ctrl_c)

    # fmt: off
    assert capsys.readouterr().out == (
        "Stopping...\n"
        "Log stream hasn't terminated; log output may be corrupted.\n"
    )
    # fmt: on

    monkeypatched_streamer_should_exit.set()


def test_stdout_closes_unexpectedly(mock_sub, popen_process, monkeypatch, capsys):
    """Streamer silently exits from ValueError because stdout was closed."""

    def monkeypatch_ensure_str(value):
        """Close stdout when ensure_str() runs on output from readline()."""
        popen_process.stdout.close()
        return value

    popen_process.stdout = StringIO(initial_value="output line 1\noutput line 2")
    monkeypatch.setattr(subprocess, "ensure_str", monkeypatch_ensure_str)

    mock_sub.stream_output("testing", popen_process)

    assert capsys.readouterr().out == "output line 1\n"
