import pytest


def test_wait_bar_done_message(console, capsys):
    """Custom done_message is printed when wait bar normally exits."""
    with console.wait_bar("Wait message...", done_message="finished"):
        pass

    assert capsys.readouterr().out == "\nWait message... finished\n"


@pytest.mark.parametrize(
    ("message", "transient", "output"),
    (
        ("Wait message...", False, "\nWait message... done\n"),
        ("", False, "\n"),
        ("Wait Message...", True, "\n"),
        ("", True, "\n"),
    ),
)
def test_wait_bar_transient(console, message, transient, output, capsys):
    """Output is present or absent based on presence of message and transient
    value."""
    with console.wait_bar(message, transient=transient):
        pass

    assert capsys.readouterr().out == output


@pytest.mark.parametrize(
    ("message", "transient", "output"),
    (
        ("Wait message...", False, "\nWait message...\n"),
        ("", False, "\n"),
        ("Wait Message...", True, "\n"),
        ("", True, "\n"),
    ),
)
def test_wait_bar_keyboard_interrupt(console, message, transient, output, capsys):
    """If the wait bar is interrupted, output is present or absent based on
    presence of message and transient value."""
    with pytest.raises(KeyboardInterrupt):
        with console.wait_bar(message, transient=transient):
            raise KeyboardInterrupt

    assert capsys.readouterr().out == output
