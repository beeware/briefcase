import pytest


def test_wait_bar_done_message(console, capsys):
    """Custom done_message is printed when wait bar normally exits."""
    with console.wait_bar("Wait message...", done_message="finished"):
        pass

    assert capsys.readouterr().out == "Wait message... finished\n"


def test_wait_bar_done_message_nested(console, capsys):
    """Custom done_message is printed when wait bar normally exits."""
    with console.wait_bar("Wait message 1...", done_message="finished"):
        with console.wait_bar("Wait message 2...", done_message="finished"):
            pass

    # fmt: off
    assert capsys.readouterr().out == (
        "Wait message 2... finished\n"
        "Wait message 1... finished\n"
    )
    # fmt: on


@pytest.mark.parametrize(
    ("message", "transient", "output"),
    (
        ("Wait message...", False, "Wait message... done\n"),
        ("", False, ""),
        ("Wait Message...", True, ""),
        ("", True, ""),
    ),
)
def test_wait_bar_transient(console, message, transient, output, capsys):
    """Output is present or absent based on presence of message and transient
    value."""
    with console.wait_bar(message, transient=transient):
        pass

    assert capsys.readouterr().out == output


@pytest.mark.parametrize(
    ("message_one", "message_two", "transient", "output"),
    (
        (
            "Wait message 1...",
            "Wait message 2...",
            False,
            "Wait message 2... done\n" "Wait message 1... done\n",
        ),
        ("", "", False, ""),
        ("Wait message 1...", "Wait message 2...", True, ""),
        ("", "", True, ""),
    ),
)
def test_wait_bar_transient_nested(
    console,
    message_one,
    message_two,
    transient,
    output,
    capsys,
):
    """Output is present or absent based on presence of message and transient
    value."""
    with console.wait_bar(message_one, transient=transient):
        with console.wait_bar(message_two, transient=transient):
            pass

    assert capsys.readouterr().out == output


@pytest.mark.parametrize(
    ("message", "transient", "output"),
    (
        ("Wait message...", False, "Wait message...\n"),
        ("", False, ""),
        ("Wait Message...", True, ""),
        ("", True, ""),
    ),
)
def test_wait_bar_keyboard_interrupt(console, message, transient, output, capsys):
    """If the wait bar is interrupted, output is present or absent based on
    presence of message and transient value."""
    with pytest.raises(KeyboardInterrupt):
        with console.wait_bar(message, transient=transient):
            raise KeyboardInterrupt

    assert capsys.readouterr().out == output


@pytest.mark.parametrize(
    ("message_one", "message_two", "transient", "output"),
    (
        (
            "Wait message 1...",
            "Wait message 2...",
            False,
            "Wait message 2...\nWait message 1...\n",
        ),
        ("", "", False, ""),
        ("Wait message 1...", "Wait message 2...", True, ""),
        ("", "", True, ""),
    ),
)
def test_wait_bar_keyboard_interrupt_nested(
    console,
    message_one,
    message_two,
    transient,
    output,
    capsys,
):
    """If the wait bar is interrupted, output is present or absent based on
    presence of message and transient value."""
    with pytest.raises(KeyboardInterrupt):
        with console.wait_bar(message_one, transient=transient):
            with console.wait_bar(message_two, transient=transient):
                raise KeyboardInterrupt

    assert capsys.readouterr().out == output
