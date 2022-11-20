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
