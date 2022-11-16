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
            "==================== 10 failed, 40 passed, 20 skipped in 124.34s ====================",
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
    ),
)
def test_default_failure_filter(recent_history):
    "The default failure filter captures known test suite failure output"
    failure_func = LogFilter.test_suite_failure(None)
    success_func = LogFilter.test_suite_success(None)

    tail = "\n".join(recent_history)
    assert not success_func(tail)
    assert failure_func(tail)


def test_custom_failure_filter():
    "The user can specify a custom failure filter"
    failure_func = LogFilter.test_suite_success("FAILURE")

    recent = [
        "rootdir: /Users/rkm/beeware/briefcase, configfile: pyproject.toml",
        "plugins: cov-3.0.0",
        "collecting ... collected 0 items",
        "",
        "============================ no tests ran in 0.01s =============================",
    ]

    assert not failure_func("\n".join(recent))

    # Add an extra line that *will* match the filter
    recent.append("I will now say the magic word, which is FAILURE, so we fail")
    assert failure_func("\n".join(recent))
