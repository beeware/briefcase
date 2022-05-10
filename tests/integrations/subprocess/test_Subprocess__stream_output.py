import pytest
from unittest import mock

from briefcase.console import Log


@pytest.fixture
def popen_process():
    process = mock.MagicMock()

    # There are extra empty strings at the end to simulate readline
    # continuously returning "" once it reaches EOF
    process.stdout.readline.side_effect = [
        "output line 1\n",
        "\n",
        "output line 3\n",
        "",
        "",
        "",
        "",
        "",
        ""
    ]
    process.poll.side_effect = [None, None, None, -3]

    return process


def test_output(mock_sub, popen_process, capsys):
    "Readline output is printed"
    mock_sub.stream_output('testing', popen_process)
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )


def test_output_debug(mock_sub, popen_process, capsys):
    "Readline output is printed; debug mode should not add extra output"
    mock_sub.command.logger = Log(verbosity=2)

    mock_sub.stream_output('testing', popen_process)
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )


def test_output_deep_debug(mock_sub, popen_process, capsys):
    "Readline output is printed with debug return code in deep debug mode"
    mock_sub.command.logger = Log(verbosity=3)

    mock_sub.stream_output('testing', popen_process)
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
        ">>> Return code: -3\n"
    )


def test_keyboard_interrupt(mock_sub, popen_process, capsys):
    "Process is terminated if user sends CTRL+C"
    popen_process.stdout.readline.side_effect = ["output line 1\n", "\n", KeyboardInterrupt()]
    mock_sub.cleanup = mock.MagicMock()

    mock_sub.stream_output("testing", popen_process)

    # Response to the CTRL-C is a process cleanup.
    mock_sub.cleanup.assert_called_once_with("testing", popen_process)

    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
    )


def test_process_exit_with_queued_output(mock_sub, popen_process, capsys):
    "All output is printed despite the process exiting early"
    popen_process.poll.side_effect = [None, -3, -3, -3]

    mock_sub.stream_output('testing', popen_process)
    assert capsys.readouterr().out == (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
