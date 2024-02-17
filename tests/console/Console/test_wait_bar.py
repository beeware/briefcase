from unittest.mock import MagicMock

import pytest

import briefcase.console


def test_wait_bar_done_message_interactive(console, capsys):
    """Custom done_message is printed when wait bar normally exits."""
    with console.wait_bar("Wait message...", done_message="finished"):
        pass

    assert capsys.readouterr().out == "Wait message... finished\n\n"


def test_wait_bar_done_message_non_interactive(non_interactive_console, capsys):
    """Custom done_message is printed when wait bar normally exits."""
    with non_interactive_console.wait_bar("Wait message...", done_message="finished"):
        pass

    assert capsys.readouterr().out == (
        "Wait message... started\n" "Wait message... finished\n\n"
    )


def test_wait_bar_done_message_nested_interactive(console, capsys):
    """Custom done_message is printed when wait bar normally exits."""
    with console.wait_bar("Wait message 1...", done_message="finished"):
        with console.wait_bar("Wait message 2...", done_message="finished"):
            pass

    expected = "Wait message 2... finished\n" "Wait message 1... finished\n\n"
    assert capsys.readouterr().out == expected


def test_wait_bar_done_message_nested_non_interactive(non_interactive_console, capsys):
    """Custom done_message is printed when wait bar normally exits."""
    with non_interactive_console.wait_bar("Wait message 1...", done_message="finished"):
        with non_interactive_console.wait_bar(
            "Wait message 2...", done_message="finished"
        ):
            pass

    expected = (
        "Wait message 1... started\n"
        "Wait message 2... started\n"
        "Wait message 2... finished\n"
        "Wait message 1... finished\n\n"
    )
    assert capsys.readouterr().out == expected


@pytest.mark.parametrize(
    ("message", "transient", "output"),
    (
        ("Wait message...", False, "Wait message... done\n\n"),
        ("", False, "\n"),
        ("Wait Message...", True, "\n"),
        ("", True, "\n"),
    ),
)
def test_wait_bar_transient_interactive(console, message, transient, output, capsys):
    """Output is present or absent based on presence of message and transient value."""
    with console.wait_bar(message, transient=transient):
        pass

    assert capsys.readouterr().out == output


@pytest.mark.parametrize(
    ("message", "transient", "output"),
    (
        ("Wait message...", False, "Wait message... started\nWait message... done\n\n"),
        ("", False, "\n"),
        ("Wait message...", True, "Wait message... started\nWait message... done\n\n"),
        ("", True, "\n"),
    ),
)
def test_wait_bar_transient_non_interactive(
    non_interactive_console,
    message,
    transient,
    output,
    capsys,
):
    """Output is present or absent based on presence of message and transient value."""
    with non_interactive_console.wait_bar(message, transient=transient):
        pass

    assert capsys.readouterr().out == output


@pytest.mark.parametrize(
    ("message_one", "message_two", "transient", "output"),
    (
        (
            "Wait message 1...",
            "Wait message 2...",
            False,
            "Wait message 2... done\nWait message 1... done\n\n",
        ),
        ("", "", False, "\n"),
        ("Wait message 1...", "Wait message 2...", True, "\n"),
        ("", "", True, "\n"),
    ),
)
def test_wait_bar_transient_nested_interactive(
    console,
    message_one,
    message_two,
    transient,
    output,
    capsys,
):
    """Output is present or absent based on presence of message and transient value."""
    with console.wait_bar(message_one, transient=transient):
        with console.wait_bar(message_two, transient=transient):
            pass

    assert capsys.readouterr().out == output


@pytest.mark.parametrize(
    ("message_one", "message_two", "transient", "output"),
    (
        (
            "Wait message 1...",
            "Wait message 2...",
            False,
            (
                "Wait message 1... started\n"
                "Wait message 2... started\n"
                "Wait message 2... done\n"
                "Wait message 1... done\n\n"
            ),
        ),
        ("", "", False, "\n"),
        (
            "Wait message 1...",
            "Wait message 2...",
            True,
            (
                "Wait message 1... started\n"
                "Wait message 2... started\n"
                "Wait message 2... done\n"
                "Wait message 1... done\n\n"
            ),
        ),
        ("", "", True, "\n"),
    ),
)
def test_wait_bar_transient_nested_non_interactive(
    non_interactive_console,
    message_one,
    message_two,
    transient,
    output,
    capsys,
):
    """Output is present or absent based on presence of message and transient value."""
    with non_interactive_console.wait_bar(message_one, transient=transient):
        with non_interactive_console.wait_bar(message_two, transient=transient):
            pass

    assert capsys.readouterr().out == output


@pytest.mark.parametrize(
    ("message", "transient", "output"),
    (
        ("Wait message...", False, "Wait message... aborted\n\n"),
        ("", False, "\n"),
        ("Wait Message...", True, "\n"),
        ("", True, "\n"),
    ),
)
def test_wait_bar_keyboard_interrupt_interactive(
    console,
    message,
    transient,
    output,
    capsys,
):
    """If the wait bar is interrupted, output is present or absent based on presence of
    message and transient value."""
    with pytest.raises(KeyboardInterrupt):
        with console.wait_bar(message, transient=transient):
            raise KeyboardInterrupt

    assert capsys.readouterr().out == output


@pytest.mark.parametrize(
    ("message", "transient", "output"),
    (
        (
            "Wait message...",
            False,
            "Wait message... started\nWait message... aborted\n\n",
        ),
        ("", False, "\n"),
        (
            "Wait message...",
            True,
            "Wait message... started\nWait message... aborted\n\n",
        ),
        ("", True, "\n"),
    ),
)
def test_wait_bar_keyboard_interrupt_non_interactive(
    non_interactive_console,
    message,
    transient,
    output,
    capsys,
):
    """If the wait bar is interrupted, output is present or absent based on presence of
    message and transient value."""
    with pytest.raises(KeyboardInterrupt):
        with non_interactive_console.wait_bar(message, transient=transient):
            raise KeyboardInterrupt

    assert capsys.readouterr().out == output


@pytest.mark.parametrize(
    ("message_one", "message_two", "transient", "output"),
    (
        (
            "Wait message 1...",
            "Wait message 2...",
            False,
            "Wait message 2... aborted\nWait message 1... aborted\n\n",
        ),
        ("", "", False, "\n"),
        ("Wait message 1...", "Wait message 2...", True, "\n"),
        ("", "", True, "\n"),
    ),
)
def test_wait_bar_keyboard_interrupt_nested_interactive(
    console,
    message_one,
    message_two,
    transient,
    output,
    capsys,
):
    """If the wait bar is interrupted, output is present or absent based on presence of
    message and transient value."""
    with pytest.raises(KeyboardInterrupt):
        with console.wait_bar(message_one, transient=transient):
            with console.wait_bar(message_two, transient=transient):
                raise KeyboardInterrupt

    assert capsys.readouterr().out == output


@pytest.mark.parametrize(
    ("message_one", "message_two", "transient", "output"),
    (
        (
            "Wait message 1...",
            "Wait message 2...",
            False,
            (
                "Wait message 1... started\n"
                "Wait message 2... started\n"
                "Wait message 2... aborted\n"
                "Wait message 1... aborted\n\n"
            ),
        ),
        ("", "", False, "\n"),
        (
            "Wait message 1...",
            "Wait message 2...",
            True,
            (
                "Wait message 1... started\n"
                "Wait message 2... started\n"
                "Wait message 2... aborted\n"
                "Wait message 1... aborted\n\n"
            ),
        ),
        ("", "", True, "\n"),
    ),
)
def test_wait_bar_keyboard_interrupt_nested_non_interactive(
    non_interactive_console,
    message_one,
    message_two,
    transient,
    output,
    capsys,
):
    """If the wait bar is interrupted, output is present or absent based on presence of
    message and transient value."""
    with pytest.raises(KeyboardInterrupt):
        with non_interactive_console.wait_bar(message_one, transient=transient):
            with non_interactive_console.wait_bar(message_two, transient=transient):
                raise KeyboardInterrupt

    assert capsys.readouterr().out == output


def test_wait_bar_always_interactive(console):
    """Wait Bar is not disabled when console is interactive."""
    with console.wait_bar():
        assert console._wait_bar.disable is False
        with console.wait_bar():
            assert console._wait_bar.disable is False


def test_wait_bar_non_interactive(non_interactive_console):
    """Wait Bar is disabled when console is non-interactive."""
    with non_interactive_console.wait_bar():
        assert non_interactive_console._wait_bar.disable is True
        with non_interactive_console.wait_bar():
            assert non_interactive_console._wait_bar.disable is True


def test_wait_bar_alive_messages_interactive(
    console,
    non_interactive_console,
    capsys,
    monkeypatch,
):
    """Wait Bar keep_alive prints keep alive messages."""
    for test_console in [console, non_interactive_console]:

        # initialization will set interval to a small number
        # update() will see time at a large number and print the message
        # then interval is reset back to a small number
        monkeypatch.setattr(
            briefcase.console.time,
            "time",
            MagicMock(side_effect=[0] + [1e42, 0] * 2),
        )

        with test_console.wait_bar("task") as keep_alive:
            for _ in range(2):
                keep_alive.update()

        assert capsys.readouterr().out.endswith(
            "... still waiting\n... still waiting\ntask done\n\n"
        )
        assert capsys.readouterr().out == ""
