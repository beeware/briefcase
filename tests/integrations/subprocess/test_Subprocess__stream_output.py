import time
from threading import Event
from unittest import mock

import pytest

from briefcase.console import Log


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
    mock_sub.command.logger = Log(verbosity=2)

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
    mock_sub.stream_output("testing", popen_process, stop_func=send_ctrl_c)

    # fmt: off
    assert capsys.readouterr().out == (
        "Stopping...\n"
        "Log stream hasn't terminated; log output may be corrupted.\n"
    )
    # fmt: on

    monkeypatched_streamer_should_exit.set()
