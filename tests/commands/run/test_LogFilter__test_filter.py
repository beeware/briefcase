import pytest

from briefcase.commands.run import LogFilter


@pytest.mark.parametrize(
    "recent_history, returncode",
    (
        # Zero return code
        [">>>>>>>>>> EXIT 0 <<<<<<<<<<", 0],
        # positive integer return code
        [">>>>>>>>>> EXIT 123 <<<<<<<<<<", 123],
        # Zero return code
        [">>>>>>>>>> EXIT -15 <<<<<<<<<<", -15],
        # Non-alpha return code
        [">>>>>>>>>> EXIT abc <<<<<<<<<<", -999],
        # Mixed return code
        [">>>>>>>>>> EXIT 42 and some more <<<<<<<<<<", -999],
    ),
)
def test_default_exit_filter(recent_history, returncode):
    """The default exit filter captures exit criteria."""
    exit_func = LogFilter.test_filter(LogFilter.DEFAULT_EXIT_REGEX)

    tail = "\n".join(["line 1", "line 2"] + [recent_history])
    assert exit_func(tail) == returncode


@pytest.mark.parametrize(
    "recent_history",
    (
        # No exit
        "This doesn't match",
        # Not enough chevrons
        ">>>> EXIT 3 <<<<",
        # Wrong text
        ">>>>>>>>>> EXEUNT 3 <<<<<<<<<<",
        # Extra text
        ">>>>>>>>>> EXIT 3 <<<<<<<<<< but there's more!",
    ),
)
def test_default_exit_filter_no_match(recent_history):
    """The default exit filter *doesn't* catch content that doesn't match the regex."""
    exit_func = LogFilter.test_filter(LogFilter.DEFAULT_EXIT_REGEX)

    tail = "\n".join(["line 1", "line 2"] + [recent_history])
    assert exit_func(tail) is None


def test_custom_filter():
    """The user can specify a custom exit filter."""
    custom_func = LogFilter.test_filter("WIBBLE (?P<returncode>.*) WIBBLE")

    # Custom filter doesn't match "normal" output
    recent = ["line 1", "line 2", ">>>>>>>>>> EXIT 123 <<<<<<<<<<"]
    assert custom_func("\n".join(recent)) is None

    # Custom filter does match "custom" output
    recent = ["line 1", "line 2", "WIBBLE 123 WIBBLE"]
    assert custom_func("\n".join(recent)) == 123


def test_bad_custom_filter():
    """If the custom filter doesn't capture a returncode named group, any match has a
    known return value."""
    custom_func = LogFilter.test_filter(r"WIBBLE \d+ WIBBLE")

    # Custom filter matches, but doesn't capture output
    recent = ["line 1", "line 2", "WIBBLE 123 WIBBLE"]
    assert custom_func("\n".join(recent)) == -998
