from unittest import mock

import pytest

from briefcase.commands.run import LogFilter
from briefcase.integrations.subprocess import StopStreaming


def test_default_filter():
    """A default logfilter echoes content verbatim."""
    popen = mock.MagicMock()
    log_filter = LogFilter(
        popen,
        clean_filter=None,
        clean_output=True,
        exit_filter=None,
    )

    for i in range(0, 10):
        line = f"this is line {i}"

        # Every line is returned verbatim
        assert [line] == list(log_filter(line))

    # no return code was detected
    assert log_filter.returncode is None


def test_clean_filter():
    """A cleaning filter can be used to strip content."""

    # Define a cleaning filter that strips the first 5 characters,
    # and identifies all content as Python
    def clean_filter(line):
        return line[5:], True

    popen = mock.MagicMock()
    log_filter = LogFilter(
        popen,
        clean_filter=clean_filter,
        clean_output=True,
        exit_filter=None,
    )

    for i in range(0, 10):
        line = f"this is line {i}"

        # The line has the preamble stripped
        assert [line[5:]] == list(log_filter(line))

    # no return code was detected
    assert log_filter.returncode is None


def test_clean_filter_unclean_output():
    """A cleaning filter can be used to strip content, but doesn't have to alter
    output."""

    # Define a cleaning filter that strips the first 5 characters,
    # and identifies all content as Python
    def clean_filter(line):
        return line[5:], True

    popen = mock.MagicMock()
    log_filter = LogFilter(
        popen,
        clean_filter=clean_filter,
        clean_output=False,
        exit_filter=None,
    )

    for i in range(0, 10):
        line = f"this is line {i}"

        # Every line is returned verbatim
        assert [line] == list(log_filter(line))

    # no return code was detected
    assert log_filter.returncode is None


@pytest.mark.parametrize(
    "raw, expected_output, use_content_filter, clean_output, returncode",
    [
        # Without cleaning, simple content is passed through as is.
        (
            ["1: line 1", "2: line 2", "3: line 3", "4: line 4", "5: line 5"],
            ["1: line 1", "2: line 2", "3: line 3", "4: line 4", "5: line 5"],
            False,  # don't use content filter
            False,  # don't use clean output
            None,  # no return code
        ),
        # Cleaning can be turned on without altering output
        (
            ["1: line 1", "2: line 2", "3: line 3", "4: line 4", "5: line 5"],
            ["1: line 1", "2: line 2", "3: line 3", "4: line 4", "5: line 5"],
            True,  # use content filter
            False,  # don't use clean output
            None,  # no return code
        ),
        # Dumped content is ignored, even if output isn't being cleaned
        (
            ["1: line 1", "2: line 2", "DUMP: garbage", "4: line 4", "5: line 5"],
            ["1: line 1", "2: line 2", "4: line 4", "5: line 5"],
            True,  # use content filter
            False,  # don't use clean output
            None,  # no return code
        ),
        # Output can be cleaned
        (
            ["1: line 1", "2: line 2", "3: line 3", "4: line 4", "5: line 5"],
            ["line 1", "line 2", "line 3", "line 4", "line 5"],
            True,  # use content filter
            True,  # use clean output
            None,  # no return code
        ),
        # Dumped content won't appear in cleaned output
        (
            ["1: line 1", "2: line 2", "DUMP: garbage", "4: line 4", "5: line 5"],
            ["line 1", "line 2", "line 4", "line 5"],
            True,  # use content filter
            True,  # use clean output
            None,  # no return code
        ),
        # Without cleaning, exit status won't be found
        (
            ["1: line 1", "2: line 2", "3: -----", "4: ", "5: EXIT 42", "post"],
            ["1: line 1", "2: line 2", "3: -----", "4: ", "5: EXIT 42", "post"],
            False,  # don't use content filter
            False,  # don't use clean output
            None,  # no return code due to line prefixes
        ),
        # If test output is clean without filtering, exit status can be determined
        (
            ["line 1", "line 2", "-----", "", "EXIT 42", "post"],
            ["line 1", "line 2", "-----", ""],
            False,  # don't use content filter
            False,  # don't use clean output
            42,  # exit status from raw output
        ),
        # Exit status can be found without altering output
        # Line prefixes are all even to ensure they aren't ignored
        (
            ["2: line 1", "4: line 2", "6: -----", "8: ", "10: EXIT 42", "post"],
            ["2: line 1", "4: line 2", "6: -----", "8: "],
            True,  # use content filter
            False,  # don't use clean output
            42,  # exit status
        ),
        # Exit status won't consider ignored content
        # Dumped content won't be considered
        (
            ["2: line 1", "4: -----", "DUMP: garbage", "6: ", "8: EXIT 42", "post"],
            ["2: line 1", "4: -----", "6: "],
            True,  # use content filter
            False,  # don't use clean output
            42,  # exit status
        ),
        # Exit status won't consider ignored content
        # Line 5 will be ignored, but not dumped
        (
            ["2: line 1", "4: -----", "5: Ignore this", "6: ", "8: EXIT 42", "post"],
            ["2: line 1", "4: -----", "5: Ignore this", "6: "],
            True,  # use content filter
            False,  # don't use clean output
            42,  # exit status
        ),
        # Exit status can be found with cleaned output
        # Line prefixes are all even to ensure they aren't ignored; output is clean
        (
            ["2: line 1", "4: line 2", "6: -----", "8: ", "10: EXIT 42", "post"],
            ["line 1", "line 2", "-----", ""],
            True,  # use content filter
            True,  # use clean output
            42,  # Exit status
        ),
        # Exit status won't consider ignored content
        # Dumped content won't be considered; output is clean
        (
            ["2: line 1", "4: -----", "DUMP: garbage", "6: ", "8: EXIT 42", "post"],
            ["line 1", "-----", ""],
            True,  # use content filter
            True,  # use clean output
            42,  # exit status
        ),
        # Exit status won't consider ignored content
        # Line 5 will be ignored, but not dumped; output is clean
        (
            ["2: line 1", "4: -----", "5: Ignore this", "6: ", "8: EXIT 42", "post"],
            ["line 1", "-----", "Ignore this", ""],
            True,  # use content filter
            True,  # use clean output
            42,  # exit status
        ),
        # Exit status won't be found if it occurs on ignored lines
        # Line 5 is the right pattern, but it will be marked as ignored by the cleaner
        (
            ["2: line 1", "4: line 2", "5: -----", "6: ", "8: EXIT 42", "post"],
            ["2: line 1", "4: line 2", "5: -----", "6: ", "8: EXIT 42", "post"],
            True,  # use content filter
            False,  # don't use clean output
            None,  # no return code due to line 5 not matching
        ),
    ],
)
def test_log_filter(
    raw,
    expected_output,
    use_content_filter,
    clean_output,
    returncode,
):
    """The log filter behaves as expected."""

    # Define a clean filter that removes an index at the start of the line, only
    # analyses content with an even prefix, and dumps content that starts "DUMP:"
    def clean_filter(line):
        if line.startswith("DUMP: "):
            return None
        parts = line.split(":", 1)
        try:
            line = int(parts[0])
            return " ".join(parts[1:]).strip(), line % 2 == 0
        except ValueError:
            return line, False

    # Define a custom filter that looks for specific multiline output
    exit_filter = LogFilter.test_filter(r"^-----\n\nEXIT (?P<returncode>\d+)$")

    # Set up a log stream
    popen = mock.MagicMock()
    log_filter = LogFilter(
        popen,
        clean_filter=clean_filter if use_content_filter else None,
        clean_output=clean_output,
        exit_filter=exit_filter,
    )

    # Pipe the raw output through the log filter, and capture the output
    output = []
    terminated = False
    for raw_line in raw:
        try:
            for line in log_filter(raw_line):
                output.append(line)
        except StopStreaming:
            terminated = True
            break

    # Actual output is as expected
    assert output == expected_output

    if returncode is None:
        # No success/failure condition was set; no termination condition was processed
        assert log_filter.returncode is None
        assert not terminated
    else:
        # The success/failure condition was detected, and the termination condition was processed
        assert log_filter.returncode == returncode
        assert terminated
