import time
from io import StringIO
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
    expected_output = (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output

    mock_sub.cleanup.assert_called_once_with("testing", streaming_process)


def test_keyboard_interrupt(mock_sub, streaming_process, capsys):
    """KeyboardInterrupt is suppressed if user sends CTRL+C and all output is
    printed."""

    send_ctrl_c = mock.MagicMock()
    send_ctrl_c.side_effect = [False, KeyboardInterrupt]

    with pytest.raises(KeyboardInterrupt):
        mock_sub.stream_output("testing", streaming_process, stop_func=send_ctrl_c)

    assert (
        capsys.readouterr().out == "output line 1\n"
        "\n"
        "output line 3\n"
        "Stopping...\n"
    )
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
        mock_sub,
        "_stream_output_thread",
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


def test_stdout_closes_unexpectedly(mock_sub, streaming_process, monkeypatch, capsys):
    """Streamer exits from ValueError because stdout was closed."""

    def monkeypatch_ensure_str(value):
        """Close stdout when ensure_str() runs on output from readline()."""
        streaming_process.stdout.close()
        return value

    streaming_process.stdout = StringIO(initial_value="output line 1\noutput line 2")
    monkeypatch.setattr(subprocess, "ensure_str", monkeypatch_ensure_str)

    mock_sub.stream_output("testing", streaming_process)

    assert capsys.readouterr().out == (
        "output line 1\n"
        "WARNING: stdout was unexpectedly closed while streaming output\n"
    )


def test_readline_raises_exception(mock_sub, streaming_process, monkeypatch, capsys):
    """Streamer aborts if readline() raises ValueError for reasons other than stdout
    closing."""

    def monkeypatch_ensure_str(value):
        """Simulate readline() raising an ValueError-derived exception."""
        raise UnicodeError("readline() exception")

    streaming_process.stdout = StringIO(initial_value="output line 1\noutput line 2")
    monkeypatch.setattr(subprocess, "ensure_str", monkeypatch_ensure_str)

    mock_sub.stream_output("testing", streaming_process)

    assert capsys.readouterr().out == (
        "Error while streaming output: UnicodeError: readline() exception\n"
    )


def test_filter_func(mock_sub, streaming_process, sleep_zero, capsys):
    """A filter can be added to modify an output stream."""

    # Define a filter function that converts "output" into "filtered"
    def filter_func(line):
        yield line.replace("output", "filtered")

    mock_sub.stream_output("testing", streaming_process, filter_func=filter_func)

    # fmt: off
    # Output has been transformed
    assert capsys.readouterr().out == (
        "filtered line 1\n"
        "\n"
        "filtered line 3\n"
    )
    # fmt: on

    mock_sub.cleanup.assert_called_once_with("testing", streaming_process)


def test_filter_func_reject(mock_sub, streaming_process, sleep_zero, capsys):
    """A filter that rejects lines can be added to modify an output stream."""

    # Define a filter function that ignores blank lines
    def filter_func(line):
        if len(line) == 0:
            return
        yield line

    mock_sub.stream_output("testing", streaming_process, filter_func=filter_func)

    # fmt: off
    # Output has been transformed
    assert capsys.readouterr().out == (
        "output line 1\n"
        "output line 3\n"
    )
    # fmt: on

    mock_sub.cleanup.assert_called_once_with("testing", streaming_process)


def test_filter_func_line_ends(mock_sub, streaming_process, sleep_zero, capsys):
    """Filter functions are not provided the newline."""

    # Define a filter function that redacts lines that end with 1
    # The newline is *not* included.
    def filter_func(line):
        if line.endswith("line 1"):
            yield line.replace("line 1", "**REDACTED**")
        else:
            yield line

    mock_sub.stream_output("testing", streaming_process, filter_func=filter_func)

    # fmt: off
    # Output has been transformed; newline exists in output
    assert capsys.readouterr().out == (
        "output **REDACTED**\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on

    mock_sub.cleanup.assert_called_once_with("testing", streaming_process)


def test_filter_func_line_multiple_output(
    mock_sub,
    streaming_process,
    sleep_zero,
    capsys,
):
    """Filter functions can generate multiple lines from a single input."""

    # Define a filter function that adds an extra line of content when the
    # lines that end with 1
    def filter_func(line):
        yield line
        if line.endswith("line 1"):
            yield "Extra content!"

    mock_sub.stream_output("testing", streaming_process, filter_func=filter_func)

    # fmt: off
    # Output has been transformed; newline exists in output
    assert capsys.readouterr().out == (
        "output line 1\n"
        "Extra content!\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on

    mock_sub.cleanup.assert_called_once_with("testing", streaming_process)


def test_filter_func_stop_iteration(mock_sub, streaming_process, capsys):
    """A filter can indicate that logging should stop."""

    # Define a filter function that converts "output" into "filtered",
    # and terminates streaming when a blank line is seen.
    def filter_func(line):
        if line == "":
            raise subprocess.StopStreaming()
        yield line.replace("output", "filtered")

    mock_sub.stream_output("testing", streaming_process, filter_func=filter_func)

    # fmt: off
    # Output has been transformed, but is truncated when the empty line was received.
    assert capsys.readouterr().out == (
        "filtered line 1\n"
    )
    # fmt: on

    mock_sub.cleanup.assert_called_once_with("testing", streaming_process)


def test_filter_func_output_and_stop_iteration(mock_sub, streaming_process, capsys):
    """A filter can indicate that logging should stop, and also output content."""

    # Define a filter function that converts "output" into "filtered",
    # and terminates streaming when a blank line is seen; but outputs
    # one more line before terminating.
    def filter_func(line):
        if line == "":
            yield "This should be the last line"
            raise subprocess.StopStreaming()
        yield line.replace("output", "filtered")

    mock_sub.stream_output("testing", streaming_process, filter_func=filter_func)

    # fmt: off
    # Output has been transformed, but is truncated when the empty line was received.
    assert capsys.readouterr().out == (
        "filtered line 1\n"
        "This should be the last line\n"
    )
    # fmt: on

    mock_sub.cleanup.assert_called_once_with("testing", streaming_process)


def test_filter_func_line_unexpected_error(mock_sub, streaming_process, capsys):
    """If a filter function fails, the error is caught and logged."""

    # Define a filter function that redacts lines that end with 1
    # The newline is *not* included.
    def filter_func(line):
        if not line:
            raise RuntimeError("Like something totally went wrong")
        yield line

    mock_sub.stream_output("testing", streaming_process, filter_func=filter_func)

    # fmt: off
    # Exception
    assert capsys.readouterr().out == (
        "output line 1\n"
        "Error while streaming output: RuntimeError: Like something totally went wrong\n"
    )
    # fmt: on

    mock_sub.cleanup.assert_called_once_with("testing", streaming_process)
