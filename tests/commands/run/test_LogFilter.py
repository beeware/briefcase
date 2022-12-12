from unittest import mock

import pytest

from briefcase.commands.run import LogFilter
from briefcase.integrations.subprocess import StopStreaming


def test_default_filter():
    "A default logfilter echoes content verbatim"
    popen = mock.MagicMock()
    log_filter = LogFilter(
        popen,
        clean_filter=None,
        clean_output=True,
        success_filter=None,
        failure_filter=None,
        exit_filter=None,
    )

    for i in range(0, 10):
        line = f"this is line {i}"

        # Every line is returned verbatim
        assert [line] == list(log_filter(line))

    # no signals were sent, and no test status was triggered
    popen.send_signal.assert_not_called()
    assert log_filter.success is None


def test_clean_filter():
    "A cleaning filter can be used to strip content"
    # Define a cleaning filter that strips the first 5 characters,
    # and identifies all content as Python
    def clean_filter(line):
        return line[5:], True

    popen = mock.MagicMock()
    log_filter = LogFilter(
        popen,
        clean_filter=clean_filter,
        clean_output=True,
        success_filter=None,
        failure_filter=None,
        exit_filter=None,
    )

    for i in range(0, 10):
        line = f"this is line {i}"

        # The line has the preamble stripped
        assert [line[5:]] == list(log_filter(line))

    # no signals were sent, and no test status was triggered
    popen.send_signal.assert_not_called()
    assert log_filter.success is None


def test_clean_filter_unclean_output():
    "A cleaning filter can be used to strip content, but doesn't have to alter output"
    # Define a cleaning filter that strips the first 5 characters,
    # and identifies all content as Python
    def clean_filter(line):
        return line[5:], True

    popen = mock.MagicMock()
    log_filter = LogFilter(
        popen,
        clean_filter=clean_filter,
        clean_output=False,
        success_filter=None,
        failure_filter=None,
        exit_filter=None,
    )

    for i in range(0, 10):
        line = f"this is line {i}"

        # Every line is returned verbatim
        assert [line] == list(log_filter(line))

    # no signals were sent, and no test status was triggered
    popen.send_signal.assert_not_called()
    assert log_filter.success is None


@pytest.mark.parametrize(
    "raw, expected_output, use_content_filter, clean_output, expected_success",
    [
        # Without cleaning, simple content is passed through as is.
        (
            ["1: line 1", "2: line 2", "3: line 3", "4: line 4", "5: line 5"],
            ["1: line 1", "2: line 2", "3: line 3", "4: line 4", "5: line 5"],
            False,  # don't use content filter
            False,  # don't use clean output
            None,  # no test termination
        ),
        # Cleaning can be turned on without altering output
        (
            ["1: line 1", "2: line 2", "3: line 3", "4: line 4", "5: line 5"],
            ["1: line 1", "2: line 2", "3: line 3", "4: line 4", "5: line 5"],
            True,  # use content filter
            False,  # don't use clean output
            None,  # no test termination
        ),
        # Dumped content is ignored, even if output isn't being cleaned
        (
            ["1: line 1", "2: line 2", "DUMP: garbage", "4: line 4", "5: line 5"],
            ["1: line 1", "2: line 2", "4: line 4", "5: line 5"],
            True,  # use content filter
            False,  # don't use clean output
            None,  # no test termination
        ),
        # Output can be cleaned
        (
            ["1: line 1", "2: line 2", "3: line 3", "4: line 4", "5: line 5"],
            ["line 1", "line 2", "line 3", "line 4", "line 5"],
            True,  # use content filter
            True,  # use clean output
            None,  # no test termination
        ),
        # Dumped content won't appear in cleaned output
        (
            ["1: line 1", "2: line 2", "DUMP: garbage", "4: line 4", "5: line 5"],
            ["line 1", "line 2", "line 4", "line 5"],
            True,  # use content filter
            True,  # use clean output
            None,  # no test termination
        ),
        # Without cleaning, success criteria won't be found
        (
            ["1: line 1", "2: line 2", "3: -----", "4: ", "5: SUCCESS", "post"],
            ["1: line 1", "2: line 2", "3: -----", "4: ", "5: SUCCESS", "post"],
            False,  # don't use content filter
            False,  # don't use clean output
            None,  # no test termination due to line prefixes
        ),
        # If test output is clean without filtering, success can be determined
        (
            ["line 1", "line 2", "-----", "", "SUCCESS", "post"],
            ["line 1", "line 2", "-----", "", "SUCCESS"],
            False,  # don't use content filter
            False,  # don't use clean output
            True,  # test success from raw output
        ),
        # Success criteria can be found without altering output
        # Line prefixes are all even to ensure they aren't ignored
        (
            ["2: line 1", "4: line 2", "6: -----", "8: ", "10: SUCCESS", "post"],
            ["2: line 1", "4: line 2", "6: -----", "8: ", "10: SUCCESS"],
            True,  # use content filter
            False,  # don't use clean output
            True,  # Test success
        ),
        # Success criteria won't consider ignored content
        # Dumped content won't be considered
        (
            ["2: line 1", "4: -----", "DUMP: garbage", "6: ", "8: SUCCESS", "post"],
            ["2: line 1", "4: -----", "6: ", "8: SUCCESS"],
            True,  # use content filter
            False,  # don't use clean output
            True,  # Test success
        ),
        # Success criteria won't consider ignored content
        # Line 5 will be ignored, but not dumped
        (
            ["2: line 1", "4: -----", "5: Ignore this", "6: ", "8: SUCCESS", "post"],
            ["2: line 1", "4: -----", "5: Ignore this", "6: ", "8: SUCCESS"],
            True,  # use content filter
            False,  # don't use clean output
            True,  # Test success
        ),
        # Success criteria can be found with cleaned output
        # Line prefixes are all even to ensure they aren't ignored; output is clean
        (
            ["2: line 1", "4: line 2", "6: -----", "8: ", "10: SUCCESS", "post"],
            ["line 1", "line 2", "-----", "", "SUCCESS"],
            True,  # use content filter
            True,  # use clean output
            True,  # Test success
        ),
        # Success criteria won't consider ignored content
        # Dumped content won't be considered; output is clean
        (
            ["2: line 1", "4: -----", "DUMP: garbage", "6: ", "8: SUCCESS", "post"],
            ["line 1", "-----", "", "SUCCESS"],
            True,  # use content filter
            True,  # use clean output
            True,  # Test success
        ),
        # Success criteria won't consider ignored content
        # Line 5 will be ignored, but not dumped; output is clean
        (
            ["2: line 1", "4: -----", "5: Ignore this", "6: ", "8: SUCCESS", "post"],
            ["line 1", "-----", "Ignore this", "", "SUCCESS"],
            True,  # use content filter
            True,  # use clean output
            True,  # Test success
        ),
        # Success criteria won't be found if it occurs on ignored lines
        # Line 5 is the right pattern, but it will be marked as ignored by the cleaner
        (
            ["2: line 1", "4: line 2", "5: -----", "6: ", "8: SUCCESS", "post"],
            ["2: line 1", "4: line 2", "5: -----", "6: ", "8: SUCCESS", "post"],
            True,  # use content filter
            False,  # don't use clean output
            None,  # no test termination due to line 5 not matching
        ),
        # Without cleaning, failure criteria won't be found
        (
            ["1: line 1", "2: line 2", "3: -----", "4: ", "5: SUCCESS", "post"],
            ["1: line 1", "2: line 2", "3: -----", "4: ", "5: SUCCESS", "post"],
            False,  # don't use content filter
            False,  # don't use clean output
            None,  # no test termination
        ),
        # Without cleaning, failure criteria won't be found
        (
            ["1: line 1", "2: line 2", "3: -----", "4: ", "5: FAILURE", "post"],
            ["1: line 1", "2: line 2", "3: -----", "4: ", "5: FAILURE", "post"],
            False,  # don't use content filter
            False,  # don't use clean output
            None,  # no test termination due to line prefixes
        ),
        # If test output is clean without filtering, failure can be determined
        (
            ["line 1", "line 2", "-----", "", "FAILURE", "post"],
            ["line 1", "line 2", "-----", "", "FAILURE"],
            False,  # don't use content filter
            False,  # don't use clean output
            False,  # test failure from raw output
        ),
        # failure criteria can be found without altering output
        # Line prefixes are all even to ensure they aren't ignored
        (
            ["2: line 1", "4: line 2", "6: -----", "8: ", "10: FAILURE", "post"],
            ["2: line 1", "4: line 2", "6: -----", "8: ", "10: FAILURE"],
            True,  # use content filter
            False,  # don't use clean output
            False,  # Test failure
        ),
        # failure criteria won't consider ignored content
        # Dumped content won't be considered
        (
            ["2: line 1", "4: -----", "DUMP: garbage", "6: ", "8: FAILURE", "post"],
            ["2: line 1", "4: -----", "6: ", "8: FAILURE"],
            True,  # use content filter
            False,  # don't use clean output
            False,  # Test failure
        ),
        # failure criteria won't consider ignored content
        # Line 5 will be ignored, but not dumped
        (
            ["2: line 1", "4: -----", "5: Ignore this", "6: ", "8: FAILURE", "post"],
            ["2: line 1", "4: -----", "5: Ignore this", "6: ", "8: FAILURE"],
            True,  # use content filter
            False,  # don't use clean output
            False,  # Test failure
        ),
        # failure criteria can be found with cleaned output
        # Line prefixes are all even to ensure they aren't ignored; output is clean
        (
            ["2: line 1", "4: line 2", "6: -----", "8: ", "10: FAILURE", "post"],
            ["line 1", "line 2", "-----", "", "FAILURE"],
            True,  # use content filter
            True,  # use clean output
            False,  # Test failure
        ),
        # failure criteria won't consider ignored content
        # Dumped content won't be considered; output is clean
        (
            ["2: line 1", "4: -----", "DUMP: garbage", "6: ", "8: FAILURE", "post"],
            ["line 1", "-----", "", "FAILURE"],
            True,  # use content filter
            True,  # use clean output
            False,  # Test failure
        ),
        # failure criteria won't consider ignored content
        # Line 5 will be ignored, but not dumped; output is clean
        (
            ["2: line 1", "4: -----", "5: Ignore this", "6: ", "8: FAILURE", "post"],
            ["line 1", "-----", "Ignore this", "", "FAILURE"],
            True,  # use content filter
            True,  # use clean output
            False,  # Test failure
        ),
        # Without cleaning, failure criteria won't be found
        (
            ["1: line 1", "2: line 2", "3: -----", "4: ", "5: FAILURE", "post"],
            ["1: line 1", "2: line 2", "3: -----", "4: ", "5: FAILURE", "post"],
            False,  # don't use content filter
            False,  # don't use clean output
            None,  # no test termination
        ),
        # Failure criteria won't be found if it occurs on ignored lines
        # Line 5 is the right pattern, but it will be marked as ignored by the cleaner
        (
            ["2: line 1", "4: line 2", "5: -----", "6: ", "8: FAILURE", "post"],
            ["2: line 1", "4: line 2", "5: -----", "6: ", "8: FAILURE", "post"],
            True,  # use content filter
            False,  # don't use clean output
            None,  # no test termination due to line 5 not matching
        ),
        # Success criteria after failure criteria is ignored because the initial
        # failure is an implicit exit
        (
            ["line 1", "line 2", "-----", "", "FAILURE", "-----", "", "SUCCESS"],
            ["line 1", "line 2", "-----", "", "FAILURE"],
            False,  # use content filter
            False,  # use clean output
            False,  # Test failure
        ),
        # Failure criteria after success criteria is ignored because the initial
        # success is an implicit exit
        (
            ["line 1", "line 2", "-----", "", "SUCCESS", "-----", "", "FAILURE"],
            ["line 1", "line 2", "-----", "", "SUCCESS"],
            False,  # use content filter
            False,  # use clean output
            True,  # Test success
        ),
    ],
)
def test_log_filter(
    raw,
    expected_output,
    use_content_filter,
    clean_output,
    expected_success,
):
    "The log filter behaves as expected"
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

    # Define a custom filters that looks for specific multiline output
    success_filter = LogFilter.test_filter(r"^-----\n\nSUCCESS$")
    failure_filter = LogFilter.test_filter(r"^-----\n\nFAILURE$")

    # Set up a log stream
    popen = mock.MagicMock()
    log_filter = LogFilter(
        popen,
        clean_filter=clean_filter if use_content_filter else None,
        clean_output=clean_output,
        success_filter=success_filter,
        failure_filter=failure_filter,
        exit_filter=None,
    )

    # Pipe the raw output through the log filter, and capture the output
    output = []
    terminated = False
    for line in raw:
        try:
            for line in log_filter(line):
                output.append(line)
        except StopStreaming:
            terminated = True
            break

    # Actual output is as expected
    assert output == expected_output

    if expected_success is None:
        # No success/failure condition was set; no termination condition was processed
        assert log_filter.success is None
        assert not terminated
    else:
        # The success/failure condition was detected, and the termination condition was processed
        assert log_filter.success == expected_success
        assert terminated


@pytest.mark.parametrize(
    "raw, expected_output, expected_success, expected_termination",
    [
        # No success, failure or exit
        (
            ["line 1", "line 2", "line 3", "line 4", "line 5"],
            ["line 1", "line 2", "line 3", "line 4", "line 5"],
            None,
            False,
        ),
        # Success, but no exit
        (
            ["line 1", "SUCCESS", "line 5"],
            ["line 1", "SUCCESS", "line 5"],
            True,
            False,
        ),
        # Failure, but no exit
        (
            ["line 1", "FAILURE", "line 5"],
            ["line 1", "FAILURE", "line 5"],
            False,
            False,
        ),
        # No result, with exit
        (
            ["line 1", "line 2", "line 3", "EXIT", "post"],
            ["line 1", "line 2", "line 3", "EXIT"],
            None,
            True,
        ),
        # Success, with exit
        (
            ["line 1", "SUCCESS", "line 5", "EXIT", "post"],
            ["line 1", "SUCCESS", "line 5", "EXIT"],
            True,
            True,
        ),
        # Failure, with exit
        (
            ["line 1", "FAILURE", "line 5", "EXIT", "post"],
            ["line 1", "FAILURE", "line 5", "EXIT"],
            False,
            True,
        ),
        # Failure then success (but no exit) records as a failure
        (
            ["line 1", "FAILURE", "line 3", "SUCCESS", "line 5"],
            ["line 1", "FAILURE", "line 3", "SUCCESS", "line 5"],
            False,
            False,
        ),
        # Success then failure (but no exit) records as a success
        (
            ["line 1", "SUCCESS", "line 3", "FAILURE", "line 5"],
            ["line 1", "SUCCESS", "line 3", "FAILURE", "line 5"],
            True,
            False,
        ),
    ],
)
def test_exit_filter(raw, expected_output, expected_success, expected_termination):
    "An exit filter"

    # Define custom filters that looks for specific output
    success_filter = LogFilter.test_filter(r"\nSUCCESS$")
    failure_filter = LogFilter.test_filter(r"\nFAILURE$")
    exit_filter = LogFilter.test_filter(r"\nEXIT$")

    # Set up a log stream
    popen = mock.MagicMock()
    log_filter = LogFilter(
        popen,
        clean_filter=None,
        clean_output=True,
        success_filter=success_filter,
        failure_filter=failure_filter,
        exit_filter=exit_filter,
    )

    # Pipe the raw output through the log filter, and capture the output
    output = []
    terminated = False
    for line in raw:
        try:
            for line in log_filter(line):
                output.append(line)
        except StopStreaming:
            terminated = True
            break

    # Actual output is as expected
    assert output == expected_output

    if expected_success is None:
        # No success/failure condition was set; no termination condition was processed
        assert log_filter.success is None
    else:
        # The success/failure condition was detected, and the termination condition was processed
        assert log_filter.success == expected_success

    assert terminated == expected_termination
