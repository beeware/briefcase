import pytest

from briefcase.platforms.macOS.filters import nslog_clean_filter


@pytest.mark.parametrize(
    ("original", "filtered"),
    [
        # An NSLog message from the app launcher is cleaned, but isn't Python output
        (
            (
                "2026-10-29 20:11:38.101 Briefcase Test[3622:722121] "
                "Running app module: briefcase_test"
            ),
            ("Running app module: briefcase_test", False),
        ),
        # Python output is included for analysis
        (
            ">>>>>>>>>> EXIT 0 <<<<<<<<<<",
            (">>>>>>>>>> EXIT 0 <<<<<<<<<<", True),
        ),
    ],
)
def test_filter(original, filtered):
    """NSLog prefixes are stripped from console output."""
    assert nslog_clean_filter(original) == filtered
