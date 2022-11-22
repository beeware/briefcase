from unittest import mock

import pytest

from briefcase.commands.run import LogFilter
from briefcase.exceptions import BriefcaseCommandError, BriefcaseTestSuiteFailure


def test_run_app(run_command, first_app):
    """An app can have it's logs streamed."""
    popen = mock.MagicMock()
    popen.returncode = 0
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Stream the app logs
    run_command._stream_app_logs(
        first_app,
        popen=popen,
        test_mode=False,
        clean_filter=clean_filter,
        clean_output=False,
        stop_func=stop_func,
    )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.success_filter is None
    assert filter_func.failure_filter is None


def test_test_mode_success(run_command, first_app):
    """An app can be streamed in test mode."""
    popen = mock.MagicMock()
    popen.returncode = 0
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Mock effect of streaming the app resulting in a test suite success
    def mock_stream_output(label, popen_process, filter_func, **kwargs):
        filter_func.success = True

    run_command.tools.subprocess.stream_output.side_effect = mock_stream_output

    # Stream the app logs
    run_command._stream_app_logs(
        first_app,
        popen=popen,
        test_mode=True,
        clean_filter=clean_filter,
        clean_output=False,
        stop_func=stop_func,
    )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.success_filter.regex.pattern == LogFilter.DEFAULT_SUCCESS_REGEX
    assert filter_func.failure_filter.regex.pattern == LogFilter.DEFAULT_FAILURE_REGEX


def test_test_mode_failure(run_command, first_app):
    """An app can be streamed in test mode, resulting in test failure."""
    popen = mock.MagicMock()
    popen.returncode = 0
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Mock effect of streaming the app resulting in a test suite success
    def mock_stream_output(label, popen_process, filter_func, **kwargs):
        filter_func.success = False

    run_command.tools.subprocess.stream_output.side_effect = mock_stream_output

    # Streaming the app logs causes a test suite failure
    with pytest.raises(BriefcaseTestSuiteFailure):
        run_command._stream_app_logs(
            first_app,
            popen=popen,
            test_mode=True,
            clean_filter=clean_filter,
            clean_output=False,
            stop_func=stop_func,
        )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.success_filter.regex.pattern == LogFilter.DEFAULT_SUCCESS_REGEX
    assert filter_func.failure_filter.regex.pattern == LogFilter.DEFAULT_FAILURE_REGEX


def test_test_mode_no_result(run_command, first_app):
    """An app can be streamed in test mode, but with no test result being
    found."""
    popen = mock.MagicMock()
    popen.returncode = 0
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Mock effect of streaming the app but not finding a test result.
    def mock_stream_output(label, popen_process, filter_func, **kwargs):
        filter_func.success = None

    run_command.tools.subprocess.stream_output.side_effect = mock_stream_output

    # Stream the app logs raises an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Test suite didn't report a result.",
    ):
        run_command._stream_app_logs(
            first_app,
            popen=popen,
            test_mode=True,
            clean_filter=clean_filter,
            clean_output=False,
            stop_func=stop_func,
        )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.success_filter.regex.pattern == LogFilter.DEFAULT_SUCCESS_REGEX
    assert filter_func.failure_filter.regex.pattern == LogFilter.DEFAULT_FAILURE_REGEX


def test_test_mode_custom_filters(run_command, first_app):
    """An app can define custom success/failure regexes."""
    popen = mock.MagicMock()
    popen.returncode = 0
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Mock effect of streaming the app resulting in a test suite success
    def mock_stream_output(label, popen_process, filter_func, **kwargs):
        filter_func.success = True

    run_command.tools.subprocess.stream_output.side_effect = mock_stream_output

    first_app.test_success_regex = "THIS IS WHAT SUCCESS LOOKS LIKE"
    first_app.test_failure_regex = "THIS IS WHAT FAILURE LOOKS LIKE"

    # Stream the app logs
    run_command._stream_app_logs(
        first_app,
        popen=popen,
        test_mode=True,
        clean_filter=clean_filter,
        clean_output=False,
        stop_func=stop_func,
    )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.success_filter.regex.pattern == "THIS IS WHAT SUCCESS LOOKS LIKE"
    assert filter_func.failure_filter.regex.pattern == "THIS IS WHAT FAILURE LOOKS LIKE"


def test_run_app_failure(run_command, first_app):
    """If an app exits with a bad exit code, that is raised as an error."""
    popen = mock.MagicMock()
    popen.returncode = 1
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Streaming the app logs raises an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Problem running app first.",
    ):
        run_command._stream_app_logs(
            first_app,
            popen=popen,
            test_mode=False,
            clean_filter=clean_filter,
            clean_output=False,
            stop_func=stop_func,
        )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.success_filter is None
    assert filter_func.failure_filter is None


def test_run_app_log_stream_failure(run_command, first_app):
    """If a log stream returns an error code, it is ignored."""
    popen = mock.MagicMock()
    popen.returncode = 1
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # The log stream raises an error code, but that doesn't raise an error
    run_command._stream_app_logs(
        first_app,
        popen=popen,
        test_mode=False,
        clean_filter=clean_filter,
        clean_output=False,
        stop_func=stop_func,
        log_stream=True,
    )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="log stream",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.success_filter is None
    assert filter_func.failure_filter is None


def test_run_app_ctrl_c(run_command, first_app):
    """An app can have it's logs streamed, but be interrupted."""
    popen = mock.MagicMock()
    popen.returncode = 0
    clean_filter = mock.MagicMock()
    stop_func = mock.MagicMock()
    run_command.tools.subprocess.stream_output = mock.MagicMock()

    # Mock a CTRL-C
    run_command.tools.subprocess.stream_output.side_effect = KeyboardInterrupt

    # Stream the app logs
    run_command._stream_app_logs(
        first_app,
        popen=popen,
        test_mode=False,
        clean_filter=clean_filter,
        clean_output=False,
        stop_func=stop_func,
    )

    # The log was streamed
    run_command.tools.subprocess.stream_output.assert_called_once_with(
        label="first",
        popen_process=popen,
        filter_func=mock.ANY,
        stop_func=stop_func,
    )

    # The filter function has the properties we'd expect
    filter_func = run_command.tools.subprocess.stream_output.mock_calls[0].kwargs[
        "filter_func"
    ]
    assert not filter_func.clean_output
    assert filter_func.clean_filter == clean_filter
    assert filter_func.success_filter is None
    assert filter_func.failure_filter is None
