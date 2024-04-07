import pytest

from briefcase.console import Console


@pytest.mark.parametrize(
    "in_text, out_text",
    [
        (
            "There is nothing wrong with your television set.",
            "There is nothing wrong with your television set.",
        ),
        (
            "There is nothing wrong with your television set.\n"
            "Do not attempt to adjust the picture.",
            "There is nothing wrong with your television set.\n"
            "Do not attempt to adjust the picture.",
        ),
        (
            "There is nothing\n\n\nwrong with your television set.\n\n"
            "Do not attempt to adjust the picture. We are controlling transmission. If we wish to make it louder, "
            "we will bring\nup the volume.\n",
            "There is nothing\n"
            "\n"
            "\n"
            "wrong with your television set.\n"
            "\n"
            "Do not attempt to adjust the picture. We are controlling transmission. If we\n"
            "wish to make it louder, we will bring\n"
            "up the volume.",
        ),
        (
            "There is nothing wrong with your television set. Do not "
            "attempt to adjust the picture. We are controlling transmission. "
            "If we wish to make it louder, we will bring up the volume. If "
            "we wish to make it softer, we will tune it to "
            "a whisper. We will control the horizontal. We will control the vertical. "
            "We can roll the image, make it flutter. We can change the "
            "focus to a soft blur or sharpen it to crystal clarity. For the next "
            "hour, sit quietly, and we will control all that you see and hear. We repeat: There is nothing "
            "wrong with your television set.",
            "There is nothing wrong with your television set. Do not attempt to adjust the\n"
            "picture. We are controlling transmission. If we wish to make it louder, we\n"
            "will bring up the volume. If we wish to make it softer, we will tune it to a\n"
            "whisper. We will control the horizontal. We will control the vertical. We can\n"
            "roll the image, make it flutter. We can change the focus to a soft blur or\n"
            "sharpen it to crystal clarity. For the next hour, sit quietly, and we will\n"
            "control all that you see and hear. We repeat: There is nothing wrong with your\n"
            "television set.",
        ),
    ],
)
def test_textwrap(in_text, out_text):
    """Text is formatted as expected."""
    assert Console().textwrap(in_text) == out_text


def test_textwrap_width_override():
    """Width override is respected."""
    in_text = "This is 27 characters long."
    out_text = "This is 27\ncharacters long."

    assert Console().textwrap(in_text, width=20) == out_text
