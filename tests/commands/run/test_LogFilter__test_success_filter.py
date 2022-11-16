import pytest

from briefcase.commands.run import LogFilter


@pytest.mark.parametrize(
    "recent_history",
    (
        # Unittest
        # - Simple pass
        [
            "----------------------------------------------------------------------",
            "Ran 5 tests in 0.000s",
            "",
            "OK",
        ],
        # - Pass with skips
        [
            "----------------------------------------------------------------------",
            "Ran 6 tests in 0.000s",
            "",
            "OK (skipped=1)",
        ],
        # - Pass with expected failure
        [
            "----------------------------------------------------------------------",
            "Ran 6 tests in 0.000s",
            "",
            "OK (expected failures=1)",
        ],
        # - Pass skips and expected failure
        [
            "----------------------------------------------------------------------",
            "Ran 7 tests in 0.000s",
            "",
            "OK (skipped=1, expected failures=1)",
        ],
        # - Large long running suite
        [
            "----------------------------------------------------------------------",
            "Ran 70 tests in 123.456s",
            "",
            "OK (skipped=10, expected failures=10)",
        ],
        # - No tests
        [
            "----------------------------------------------------------------------",
            "Ran 0 tests in 0.000s",
            "",
            "OK",
        ],
        # Pytest
        # - Only passes
        [
            "tests/foobar/test_other.py::test_pass2 PASSED                             [ 71%]",
            "tests/foobar/test_things.py::test_pass1 PASSED                            [ 85%]",
            "tests/foobar/test_things.py::test_pass2 PASSED                            [100%]",
            "",
            "============================== 7 passed in 0.01s ===============================",
        ],
        # - Passes and skips
        [
            "tests/foobar/test_other.py::test_pass2 PASSED                             [ 71%]",
            "tests/foobar/test_things.py::test_pass1 PASSED                            [ 85%]",
            "tests/foobar/test_things.py::test_pass2 PASSED                            [100%]",
            "",
            "========================= 5 passed, 2 skipped in 0.02s =========================",
        ],
        # - Lots of Passes and skips, in a long running suite
        [
            "tests/foobar/test_other.py::test_pass2 PASSED                             [ 71%]",
            "tests/foobar/test_things.py::test_pass1 PASSED                            [ 85%]",
            "tests/foobar/test_things.py::test_pass2 PASSED                            [100%]",
            "",
            "======================= 50 passed, 20 skipped in 123.45s =======================",
        ],
        # - No tests
        [
            "rootdir: /Users/rkm/beeware/briefcase, configfile: pyproject.toml",
            "plugins: cov-3.0.0",
            "collecting ... collected 0 items",
            "",
            "============================ no tests ran in 0.01s =============================",
        ],
    ),
)
def test_default_success_filter(recent_history):
    "The default success filter captures known test suite success output"
    failure_func = LogFilter.test_filter(LogFilter.DEFAULT_FAILURE_REGEX)
    success_func = LogFilter.test_filter(LogFilter.DEFAULT_SUCCESS_REGEX)

    tail = "\n".join(recent_history)
    assert success_func(tail)
    assert not failure_func(tail)


@pytest.mark.parametrize(
    "recent_history",
    (
        # Unittest
        # - OK, but without the "ran tests" part
        [
            "Some other content",
            "----------------------------------------------------------------------",
            "",
            "OK",
        ],
        # - OK, but without the "end of suite" separator
        [
            "Some other content",
            "Ran 5 tests in 0.000s",
            "",
            "OK",
        ],
    ),
)
def test_default_filter_no_match(recent_history):
    "The default success filter *doesn't* catch content that doesn't match the regex"
    success_func = LogFilter.test_filter(LogFilter.DEFAULT_SUCCESS_REGEX)

    tail = "\n".join(recent_history)
    assert not success_func(tail)
