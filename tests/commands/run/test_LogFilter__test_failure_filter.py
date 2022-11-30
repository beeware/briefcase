import pytest

from briefcase.commands.run import LogFilter


@pytest.mark.parametrize(
    "recent_history",
    (
        # Unittest
        # - Failures
        [
            "----------------------------------------------------------------------",
            "Ran 6 tests in 0.001s",
            "",
            "FAILED (failures=2)",
        ],
        # - Failures and skips
        [
            "----------------------------------------------------------------------",
            "Ran 7 tests in 0.000s",
            "",
            "FAILED (failures=2, skipped=1)",
        ],
        # - Failures and expected failures
        [
            "----------------------------------------------------------------------",
            "Ran 7 tests in 0.000s",
            "",
            "FAILED (failures=1, expected failures=1)",
        ],
        # - Failures and expected failures
        [
            "----------------------------------------------------------------------",
            "Ran 6 tests in 0.001s",
            "",
            "FAILED (expected failures=1, unexpected successes=1)",
        ],
        # - Failures and expected failures
        [
            "----------------------------------------------------------------------",
            "Ran 6 tests in 0.001s",
            "",
            "FAILED (failures=1, expected failures=3, unexpected successes=1)",
        ],
        # - Failures, skips, and expected failures
        [
            "----------------------------------------------------------------------",
            "Ran 8 tests in 0.001s",
            "",
            "FAILED (failures=3, skipped=1, expected failures=1)",
        ],
        # - Failures, errors, skips and expected failures
        [
            "----------------------------------------------------------------------",
            "Ran 7 tests in 0.000s",
            "",
            "FAILED (failures=1, errors=1, skipped=1, expected failures=1)",
        ],
        # - Failures, skips, expected failures, and unexpected successes
        [
            "----------------------------------------------------------------------",
            "Ran 6 tests in 0.001s",
            "",
            "FAILED (failures=1, skipped=1, expected failures=2, unexpected successes=1)",
        ],
        # - Failures in negative time (?!)
        [
            "----------------------------------------------------------------------",
            "Ran 6 tests in -12.345s",
            "",
            "FAILED (failures=2)",
        ],
        # Pytest
        # - Only failures
        [
            "FAILED tests/foobar/test_other.py::test_fail1 - assert 1 == 2",
            "FAILED tests/foobar/test_other.py::test_fail2 - assert 1 == 2",
            "FAILED tests/foobar/test_things.py::test_fail1 - assert 1 == 2",
            "FAILED tests/foobar/test_things.py::test_fail2 - assert 1 == 2",
            "============================== 6 failed in 0.04s ===============================",
        ],
        # - Failures and skips
        [
            "",
            "tests/test_base.py:10: AssertionError",
            "=========================== short test summary info ============================",
            "FAILED tests/test_base.py::test_fail - assert 1 == 2",
            "========================= 1 failed, 6 skipped in 0.03s =========================",
        ],
        # - Failures and passes
        [
            "",
            "tests/test_base.py:10: AssertionError",
            "=========================== short test summary info ============================",
            "FAILED tests/test_base.py::test_fail - assert 1 == 2",
            "========================= 1 failed, 5 passed in 0.03s ==========================",
        ],
        # - Failures, passes and skips
        [
            "",
            "tests/test_base.py:10: AssertionError",
            "=========================== short test summary info ============================",
            "FAILED tests/test_base.py::test_fail - assert 1 == 2",
            "==================== 1 failed, 4 passed, 2 skipped in 0.03s ====================",
        ],
        # - Lots of failures, passes and skips, in a long running suite
        [
            "FAILED tests/test_base.py::test_fail7 - assert 1 == 2",
            "FAILED tests/test_base.py::test_fail8 - assert 1 == 2",
            "FAILED tests/test_base.py::test_fail9 - assert 1 == 2",
            "FAILED tests/test_base.py::test_fail10 - assert 1 == 2",
            "================== 10 failed, 40 passed, 20 skipped in 124.34s =================",
        ],
        # Failures and error
        [
            "FAILED tests/foobar/test_other.py::test_pass - assert 1 == 2",
            "FAILED tests/foobar/test_other.py::test_fail - assert 1 == 2",
            "FAILED tests/foobar/test_things.py::test_fail - assert 1 == 2",
            "ERROR tests/foobar/test_things.py::test_pass - Exception",
            "========================== 6 failed, 1 error in 0.04s ==========================",
        ],
        # Failures and errors
        [
            "FAILED tests/foobar/test_other.py::test_pass - assert 1 == 2",
            "FAILED tests/foobar/test_other.py::test_fail - assert 1 == 2",
            "ERROR tests/foobar/test_things.py::test_fail - Exception",
            "ERROR tests/foobar/test_things.py::test_pass - Exception",
            "========================== 6 failed, 2 errors in 0.04s ==========================",
        ],
        # Failures, passes, skips and error
        [
            "tests/test_base.py:9: AssertionError",
            "=========================== short test summary info ============================",
            "FAILED tests/test_base.py::test_fail - assert 1 == 2",
            "ERROR tests/foobar/test_things.py::test_pass - Exception",
            "=============== 1 failed, 2 passed, 3 skipped, 1 error in 0.05s ================",
        ],
        # Failures, skips and error
        [
            "FAILED tests/test_base.py::test_pass - assert 1 == 2",
            "FAILED tests/test_base.py::test_fail - assert 1 == 2",
            "FAILED tests/foobar/test_things.py::test_fail - assert 1 == 2",
            "ERROR tests/foobar/test_things.py::test_pass - Exception",
            "==================== 3 failed, 3 skipped, 1 error in 0.03s =====================",
        ],
        # Failures, passes and error
        [
            "FAILED tests/test_base.py::test_fail - assert 1 == 2",
            "FAILED tests/test_base.py::test_skipped - assert 1 == 2",
            "FAILED tests/foobar/test_things.py::test_fail - assert 1 == 2",
            "ERROR tests/foobar/test_things.py::test_pass - Exception",
            "===================== 4 failed, 2 passed, 1 error in 0.04s =====================",
        ],
        # Failures, passes, skips and errors
        [
            "tests/test_base.py:9: AssertionError",
            "=========================== short test summary info ============================",
            "FAILED tests/test_base.py::test_fail - assert 1 == 2",
            "FAILED tests/foobar/test_things.py::test_fail - assert 1 == 2",
            "ERROR tests/foobar/test_things.py::test_pass - Exception",
            "=============== 2 failed, 2 passed, 3 skipped, 1 error in 0.05s ================",
        ],
        # No failures, but an error
        [
            "tests/test_base.py:9: AssertionError",
            "=========================== short test summary info ============================",
            "FAILED tests/test_base.py::test_fail - assert 1 == 2",
            "FAILED tests/foobar/test_things.py::test_fail - assert 1 == 2",
            "ERROR tests/foobar/test_things.py::test_pass - Exception",
            "=================== 2 passed, 3 skipped, 1 error in 0.05s =====================",
        ],
        # No failures, but errors
        [
            "tests/test_base.py:9: AssertionError",
            "=========================== short test summary info ============================",
            "FAILED tests/test_base.py::test_fail - assert 1 == 2",
            "ERROR tests/foobar/test_things.py::test_fail - Exception",
            "ERROR tests/foobar/test_things.py::test_pass - Exception",
            "=================== 2 passed, 3 skipped, 2 errors in 0.05s =====================",
        ],
        # - Error collecting test suite
        [
            "E   NameError: name 'pytest' is not defined",
            "=========================== short test summary info ============================",
            "ERROR tests/foobar/test_other.py - NameError: name 'pytest' is not defined",
            "!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!",
            "=============================== 1 error in 0.05s ===============================",
        ],
        # - Multiple errors collecting test suite
        [
            "=========================== short test summary info ============================",
            "ERROR tests/foobar/test_other.py - NameError: name 'pytest' is not defined",
            "ERROR tests/foobar/test_things.py - NameError: name 'pytest' is not defined",
            "!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!",
            "============================== 2 errors in 0.05s ===============================",
        ],
        # - Pytest with the lot
        [
            '    assert color.to_string() == "#0025002a0045"',
            "",
            "-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html",
            "= 2 failed, 3 passed, 5 skipped, 2 deselected, 3 xfailed, 4 xpassed, 2 warnings, 4 errors in 0.68s =",
        ],
        # - Failures in negative time
        [
            "FAILED tests/foobar/test_other.py::test_fail1 - assert 1 == 2",
            "FAILED tests/foobar/test_other.py::test_fail2 - assert 1 == 2",
            "FAILED tests/foobar/test_things.py::test_fail1 - assert 1 == 2",
            "FAILED tests/foobar/test_things.py::test_fail2 - assert 1 == 2",
            "============================= 6 failed in -12.345s =============================",
        ],
        # - Failures with content after the time.
        [
            "tests/test_thirdparty.py::test_pandas PASSED                              [100%]",
            "==================== 24 failed, 5 passed in 89.65s (0:01:29) ===================",
        ],
        # Until https://github.com/chaquo/chaquopy/issues/746 is resolved, Android output
        # will contain extra line breaks because it produces a line for each call to `write`,
        # not just on newlines. The unittest regex contains extra named groups to
        # accommodate these discrepancies; those groups can be deleted once the Chaquopy
        # issue is fixed.
        [
            " ",
            "----------------------------------------------------------------------",
            " ",
            "Ran 6 tests in 0.004s",
            " ",
            " ",
            "FAILED",
            " (failures=1)",
        ],
        [
            " ",
            "----------------------------------------------------------------------",
            " ",
            "Ran 6 tests in 0.004s",
            " ",
            " ",
            "FAILED",
            " (failures=1, skipped=1, expected failures=2, unexpected successes=1)",
        ],
    ),
)
def test_default_failure_filter(recent_history):
    "The default failure filter captures known test suite failure output"
    failure_func = LogFilter.test_filter(LogFilter.DEFAULT_FAILURE_REGEX)
    success_func = LogFilter.test_filter(LogFilter.DEFAULT_SUCCESS_REGEX)

    tail = "\n".join(recent_history)
    assert not success_func(tail)
    assert failure_func(tail)


@pytest.mark.parametrize(
    "recent_history",
    (
        # Unittest
        # - FAILED, but without the "ran tests" part
        [
            "Some other content",
            "----------------------------------------------------------------------",
            "",
            "FAILED (failures=2)",
        ],
        # - FAILED, but without the "end of suite" separator
        [
            "Some other content",
            "Ran 5 tests in 0.000s",
            "",
            "FAILED (failures=2)",
        ],
    ),
)
def test_default_filter_no_match(recent_history):
    "The default failure filter *doesn't* catch content that doesn't match the regex"
    failure_func = LogFilter.test_filter(LogFilter.DEFAULT_FAILURE_REGEX)

    tail = "\n".join(recent_history)
    assert not failure_func(tail)
