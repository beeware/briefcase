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


@pytest.mark.parametrize(
    "width, in_text, out_text",
    [
        (20, "This is 27 characters long.", "This is 27\ncharacters long."),
        (
            50,
            "This is 57 characters long. This is 57 characters long.",
            "This is 57 characters long. This is 57 characters\nlong.",
        ),
        (
            80,
            "This is 83 characters long. This is 83 characters long. This is 83 characters long.",
            "This is 83 characters long. This is 83 characters long. This is 83 characters\nlong.",
        ),
        (
            120,
            "This is 144 characters long. This is 144 characters long. This is 144 characters long. "
            "This is 144 characters long. This is 144 characters long.",
            "This is 144 characters long. This is 144 characters long. "
            "This is 144 characters long. This is 144 characters long. This\nis 144 characters long.",
        ),
    ],
)
def test_textwrap_width_override(width, in_text, out_text):
    """Width override is respected."""
    assert Console().textwrap(in_text, width=width) == out_text
