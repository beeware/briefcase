import threading
from io import StringIO

import pytest

from briefcase.console import Log
from briefcase.integrations import subprocess
from briefcase.integrations.subprocess import PopenOutputStreamer


@pytest.fixture
def streamer(streaming_process):
    return PopenOutputStreamer(
        label="test",
        popen_process=streaming_process,
        logger=Log(),
    )


def test_output(streamer, capsys):
    """Process output is printed."""
    streamer.start()
    streamer.join(timeout=5)

    # fmt: off
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on


def test_stdout_closes_unexpectedly(streamer, monkeypatch, capsys):
    """Streamer exits from ValueError because stdout was closed."""

    def monkeypatch_ensure_str(value):
        """Close stdout when ensure_str() runs on output from readline()."""
        streamer.popen_process.stdout.close()
        return value

    monkeypatch.setattr(subprocess, "ensure_str", monkeypatch_ensure_str)
    streamer.popen_process.stdout = StringIO("output line 1\noutput line 2")

    streamer.start()
    streamer.join(timeout=5)

    assert capsys.readouterr().out == (
        "output line 1\n"
        "WARNING: stdout was unexpectedly closed while streaming output\n"
    )


def test_readline_raises_exception(streamer, monkeypatch, capsys):
    """Streamer aborts if readline() raises ValueError for reasons other than stdout
    closing."""

    def monkeypatch_ensure_str(value):
        """Simulate readline() raising an ValueError-derived exception."""
        raise UnicodeError("readline() exception")

    monkeypatch.setattr(subprocess, "ensure_str", monkeypatch_ensure_str)

    streamer.start()
    streamer.join(timeout=5)

    assert capsys.readouterr().out == (
        "Error while streaming output: UnicodeError: readline() exception\n"
    )


def test_request_stop(streamer, capsys):
    """Requesting the streamer to stop sets the stop flag."""
    streamer.start()
    streamer.join(timeout=5)

    # fmt: off
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on

    assert not streamer.stop_flag.is_set()

    streamer.request_stop()

    assert streamer.stop_flag.is_set()


def test_request_stop_set_immediately(streamer, capsys):
    """Nothing is printed if stop flag is immediately set."""
    streamer.request_stop()

    streamer.start()
    streamer.join(timeout=5)

    assert capsys.readouterr().out == ""


def test_request_stop_set_during_output(streamer, monkeypatch, capsys):
    """Streamer prints nothing more after stop flag is set."""

    def filter_func(value):
        """Simulate stop flag set while output is being read."""
        streamer.request_stop()
        yield value

    streamer.filter_func = filter_func

    streamer.start()
    streamer.join(timeout=5)

    assert capsys.readouterr().out == "output line 1\n"


def test_captured_output(streamer, capsys):
    """Captured output is available after streaming."""
    streamer.capture_output = True

    streamer.start()
    streamer.join(timeout=5)

    assert capsys.readouterr().out == ""

    # fmt: off
    assert streamer.captured_output == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on


def test_captured_output_interim(streamer, monkeypatch, capsys):
    """Captured output is available during streaming."""
    streamer.capture_output = True

    streamer_is_waiting = threading.Event()
    continue_streaming = threading.Event()

    def mock_readline():
        """Wait on asserts while returning output lines."""
        yield "output line 1\n"
        yield "output line 2\n"
        streamer_is_waiting.set()
        continue_streaming.wait(timeout=5)
        yield "output line 3\n"
        yield "output line 4\n"
        yield ""

    streamer.popen_process.stdout.readline.side_effect = mock_readline()

    streamer.start()
    streamer_is_waiting.wait(timeout=5)

    assert streamer.captured_output == "output line 1\noutput line 2\n"

    continue_streaming.set()
    streamer.join(timeout=5)

    assert streamer.captured_output == "output line 3\noutput line 4\n"


def test_filter_func(streamer, capsys):
    """A filter can be added to modify an output stream."""

    # Define a filter function that converts "output" into "filtered"
    def filter_func(line):
        yield line.replace("output", "filtered")

    streamer.filter_func = filter_func

    streamer.start()
    streamer.join(timeout=5)

    # fmt: off
    # Output has been transformed
    assert capsys.readouterr().out == (
        "filtered line 1\n"
        "\n"
        "filtered line 3\n"
    )
    # fmt: on


def test_filter_func_reject(streamer, capsys):
    """A filter that rejects lines can be added to modify an output stream."""

    # Define a filter function that ignores blank lines
    def filter_func(line):
        if len(line) == 0:
            return
        yield line

    streamer.filter_func = filter_func

    streamer.start()
    streamer.join(timeout=5)

    # fmt: off
    # Output has been transformed
    assert capsys.readouterr().out == (
        "output line 1\n"
        "output line 3\n"
    )
    # fmt: on


def test_filter_func_line_ends(streamer, sleep_zero, capsys):
    """Filter functions are not provided the newline."""

    # Define a filter function that redacts lines that end with 1
    # The newline is *not* included.
    def filter_func(line):
        if line.endswith("line 1"):
            yield line.replace("line 1", "**REDACTED**")
        else:
            yield line

    streamer.filter_func = filter_func

    streamer.start()
    streamer.join(timeout=5)

    # fmt: off
    # Output has been transformed; newline exists in output
    assert capsys.readouterr().out == (
        "output **REDACTED**\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on


def test_filter_func_line_multiple_output(streamer, capsys):
    """Filter functions can generate multiple lines from a single input."""

    # Define a filter function that adds an extra line of content when the
    # lines that end with 1
    def filter_func(line):
        yield line
        if line.endswith("line 1"):
            yield "Extra content!"

    streamer.filter_func = filter_func

    streamer.start()
    streamer.join(timeout=5)

    # fmt: off
    # Output has been transformed; newline exists in output
    assert capsys.readouterr().out == (
        "output line 1\n"
        "Extra content!\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on


def test_filter_func_stop_iteration(streamer, capsys):
    """A filter can indicate that logging should stop."""

    # Define a filter function that converts "output" into "filtered",
    # and terminates streaming when a blank line is seen.
    def filter_func(line):
        if line == "":
            raise subprocess.StopStreaming()
        yield line.replace("output", "filtered")

    streamer.filter_func = filter_func

    streamer.start()
    streamer.join(timeout=5)

    # fmt: off
    # Output has been transformed, but is truncated when the empty line was received.
    assert capsys.readouterr().out == (
        "filtered line 1\n"
    )
    # fmt: on


def test_filter_func_output_and_stop_iteration(streamer, capsys):
    """A filter can indicate that logging should stop, and also output content."""

    # Define a filter function that converts "output" into "filtered",
    # and terminates streaming when a blank line is seen; but outputs
    # one more line before terminating.
    def filter_func(line):
        if line == "":
            yield "This should be the last line"
            raise subprocess.StopStreaming()
        yield line.replace("output", "filtered")

    streamer.filter_func = filter_func

    streamer.start()
    streamer.join(timeout=5)

    # fmt: off
    # Output has been transformed, but is truncated when the empty line was received.
    assert capsys.readouterr().out == (
        "filtered line 1\n"
        "This should be the last line\n"
    )
    # fmt: on


def test_filter_func_line_unexpected_error(streamer, capsys):
    """If a filter function fails, the error is caught and logged."""

    # Define a filter function that raises a RunTimeError
    # The newline is *not* included.
    def filter_func(line):
        if not line:
            raise RuntimeError("Like something totally went wrong")
        yield line

    streamer.filter_func = filter_func

    streamer.start()
    streamer.join(timeout=5)

    # fmt: off
    # Exception
    assert capsys.readouterr().out == (
        "output line 1\n"
        "Error while streaming output: RuntimeError: Like something totally went wrong\n"
    )
    # fmt: on
