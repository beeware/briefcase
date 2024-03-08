from briefcase.console import LogLevel


def test_output(mock_sub, streaming_process, sleep_zero, capsys):
    """Process output is printed."""
    streamer = mock_sub.stream_output_non_blocking("testing", streaming_process)
    streamer.join()

    # fmt: off
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on


def test_output_debug(mock_sub, streaming_process, sleep_zero, capsys):
    """Process output is printed; no debug output for only
    stream_output_non_blocking."""
    mock_sub.tools.logger.verbosity = LogLevel.DEBUG

    streamer = mock_sub.stream_output_non_blocking("testing", streaming_process)
    streamer.join()

    # fmt: off
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on


def test_captured_output(mock_sub, streaming_process, sleep_zero, capsys):
    """Process output is captured and available later."""
    streamer = mock_sub.stream_output_non_blocking(
        "testing",
        streaming_process,
        capture_output=True,
    )
    streamer.join()

    assert capsys.readouterr().out == ""
    # fmt: off
    assert streamer.captured_output == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on


def test_filter_func(mock_sub, streaming_process, sleep_zero, capsys):
    """Process output can be filtered with a filter func."""

    def filter_func(line):
        """Filter out lines without text."""
        if line == "":
            return
        yield line

    streamer = mock_sub.stream_output_non_blocking(
        "testing",
        streaming_process,
        filter_func=filter_func,
    )
    streamer.join()

    # fmt: off
    assert capsys.readouterr().out == (
        "output line 1\n"
        "output line 3\n"
    )
    # fmt: on
