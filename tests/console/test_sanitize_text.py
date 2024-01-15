import pytest

from briefcase.console import sanitize_text


@pytest.mark.parametrize(
    "input_text, sanitized_text",
    [
        (
            "log output",
            "log output",
        ),
        (
            "ls\n\x1b[00m\x1b[01;31mexamplefile.zip\x1b[00m\n\x1b[01;31m",
            "ls\nexamplefile.zip\n",
        ),
        (
            "log output: \u001b[31mRed\u001B[0m",
            "log output: Red",
        ),
        (
            "\u001b[1mbold log output:\u001b[0m \u001b[4mUnderline\u001b[0m",
            "bold log output: Underline",
        ),
        (
            f"{chr(7)}{chr(8)}{chr(11)}{chr(12)}{chr(13)}log{chr(7)} output{chr(7)}",
            "log output",
        ),
    ],
)
def test_sanitize_text(input_text, sanitized_text):
    """Text is sanitized as expected."""
    assert sanitize_text(input_text) == sanitized_text
