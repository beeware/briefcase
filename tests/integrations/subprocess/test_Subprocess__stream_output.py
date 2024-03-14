import time
from threading import Event
from unittest import mock

import pytest

from briefcase.console import LogLevel
from briefcase.integrations import subprocess


@pytest.fixture()
def mock_sub(mock_sub):
    # also mock cleanup for stream output testing
    mock_sub.cleanup = mock.MagicMock()
    return mock_sub


def test_output(mock_sub, streaming_process, sleep_zero, capsys):
    """Process output is printed."""
    mock_sub.stream_output("testing", streaming_process)

    # fmt: off
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on
    mock_sub.cleanup.assert_called_once_with("testing", streaming_process)


def test_output_debug(mock_sub, streaming_process, sleep_zero, capsys):
    """Process output is printed; no debug output for only stream_output."""
    mock_sub.tools.logger.verbosity = LogLevel.DEBUG

    mock_sub.stream_output("testing", streaming_process)

    # fmt: off
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on

    mock_sub.cleanup.assert_called_once_with("testing", streaming_process)


def test_keyboard_interrupt(mock_sub, streaming_process, capsys):
    """KeyboardInterrupt is suppressed if user sends CTRL+C and all output is
    printed."""

    send_ctrl_c = mock.MagicMock()
    send_ctrl_c.side_effect = [False, KeyboardInterrupt]

    with pytest.raises(KeyboardInterrupt):
        mock_sub.stream_output("testing", streaming_process, stop_func=send_ctrl_c)

    # fmt: off
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
        "Stopping...\n"
    )
    # fmt: on
    mock_sub.cleanup.assert_called_once_with("testing", streaming_process)


def test_process_exit_with_queued_output(
    mock_sub,
    streaming_process,
    sleep_zero,
    capsys,
):
    """All output is printed despite the process exiting early."""
    streaming_process.poll.side_effect = [None, -3, -3, -3]

    mock_sub.stream_output("testing", streaming_process)

    # fmt: off
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on
    mock_sub.cleanup.assert_called_once_with("testing", streaming_process)


@pytest.mark.parametrize("stop_func_ret_val", (True, False))
def test_stop_func(mock_sub, streaming_process, stop_func_ret_val, sleep_zero, capsys):
    """All output is printed whether stop_func aborts streaming or not."""
    mock_sub.stream_output(
        "testing", streaming_process, stop_func=lambda: stop_func_ret_val
    )

    # fmt: off
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on
    mock_sub.cleanup.assert_called_once_with("testing", streaming_process)


def test_stuck_streamer(mock_sub, streaming_process, sleep_zero, monkeypatch, capsys):
    """Following a KeyboardInterrupt, output streaming returns even if the output
    streamer becomes stuck."""

    # Mock time.time() to return times that monotonically increase by 1s
    # every time it is invoked. This allows us to simulate the progress of
    # time much faster than the actual calls to time.sleep() would.
    mock_time = mock.MagicMock(side_effect=range(1000, 1005))
    monkeypatch.setattr(time, "time", mock_time)

    # Flag that Briefcase has finished simulating its waiting on the output
    # streamer to exit normally; so, it should now exit.
    monkeypatched_streamer_should_exit = Event()
    # Flag that Briefcase waited too long on the output streamer
    monkeypatched_streamer_was_improperly_awaited = Event()
    # Flag that output streamer has exited
    monkeypatched_streamer_exited = Event()

    def monkeypatched_blocked_streamer(*a, **kw):
        """Simulate a streamer that blocks longer than it will be waited on."""
        if not monkeypatched_streamer_should_exit.wait(timeout=5):
            monkeypatched_streamer_was_improperly_awaited.set()
        monkeypatched_streamer_exited.set()

    monkeypatch.setattr(
        subprocess.PopenOutputStreamer,
        "run",
        monkeypatched_blocked_streamer,
    )

    send_ctrl_c = mock.MagicMock()
    send_ctrl_c.side_effect = [False, KeyboardInterrupt]
    with pytest.raises(KeyboardInterrupt):
        mock_sub.stream_output("testing", streaming_process, stop_func=send_ctrl_c)

    monkeypatched_streamer_should_exit.set()

    # Since the waiting around for the output streamer has been
    # short-circuited, Briefcase should quickly give up waiting on
    # the output streamer and it should exit...so, confirm it does.
    assert monkeypatched_streamer_exited.wait(timeout=1)
    assert not monkeypatched_streamer_was_improperly_awaited.is_set()

    # fmt: off
    assert capsys.readouterr().out == (
        "Stopping...\n"
        "Log stream hasn't terminated; log output may be corrupted.\n"
    )
    # fmt: on
