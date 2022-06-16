from time import sleep
from unittest import mock

import pytest

from briefcase.console import Log


@pytest.fixture()
def mock_sub(mock_sub):
    # also mock cleanup for stream output testing
    mock_sub.cleanup = mock.MagicMock()
    return mock_sub


def test_output(mock_sub, popen_process, capsys):
    """Readline output is printed."""
    mock_sub.stream_output("testing", popen_process)

    assert capsys.readouterr().out == ("output line 1\n" "\n" "output line 3\n")
    mock_sub.cleanup.assert_called_once_with("testing", popen_process)


def test_output_debug(mock_sub, popen_process, capsys):
    """Readline output is printed; debug mode should not add extra output."""
    mock_sub.command.logger = Log(verbosity=2)

    mock_sub.stream_output("testing", popen_process)

    # fmt: off
    expected_output = (
        "output line 1\n"
        "\n"
        "output line 3\n"
        ">>> Return code: -3\n"
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output

    mock_sub.cleanup.assert_called_once_with("testing", popen_process)


def test_output_deep_debug(mock_sub, popen_process, capsys):
    """Readline output is printed with debug return code in deep debug mode."""
    mock_sub.command.logger = Log(verbosity=3)

    mock_sub.stream_output("testing", popen_process)

    # fmt: off
    expected_output = (
        "output line 1\n"
        "\n"
        "output line 3\n"
        ">>> Return code: -3\n"
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output

    mock_sub.cleanup.assert_called_once_with("testing", popen_process)


def test_keyboard_interrupt(mock_sub, popen_process, capsys):
    """KeyboardInterrupt is suppressed if user sends CTRL+C and all output is
    printed."""

    def slow_poll(*a):
        sleep(0.5)
        return -3

    # this helps ensure that the output streaming thread doesn't
    # finish before is_alive() is called and therefore ensures
    # that stop_func is always executed during this test.
    popen_process.poll = mock.MagicMock()
    popen_process.poll.side_effect = slow_poll

    send_ctrl_c = mock.MagicMock()
    send_ctrl_c.side_effect = [False, KeyboardInterrupt]

    mock_sub.stream_output("testing", popen_process, stop_func=send_ctrl_c)

    assert capsys.readouterr().out == ("output line 1\n" "\n" "output line 3\n")
    mock_sub.cleanup.assert_called_once_with("testing", popen_process)


def test_process_exit_with_queued_output(mock_sub, popen_process, capsys):
    """All output is printed despite the process exiting early."""
    popen_process.poll.side_effect = [None, -3, -3, -3]

    mock_sub.stream_output("testing", popen_process)
    assert capsys.readouterr().out == ("output line 1\n" "\n" "output line 3\n")
    mock_sub.cleanup.assert_called_once_with("testing", popen_process)


@pytest.mark.parametrize("stop_func_ret_val", (True, False))
def test_stop_func(mock_sub, popen_process, stop_func_ret_val, capsys):
    """All output is printed whether stop_func aborts streaming or not."""
    mock_sub.stream_output(
        "testing", popen_process, stop_func=lambda: stop_func_ret_val
    )
    assert capsys.readouterr().out == ("output line 1\n" "\n" "output line 3\n")
    mock_sub.cleanup.assert_called_once_with("testing", popen_process)
