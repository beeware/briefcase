from unittest.mock import ANY, MagicMock, Mock

import pytest

from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def mock_sub(mock_tools):
    mock_tools.input.release_console_control = Mock(
        wraps=mock_tools.input.release_console_control
    )
    mock_sub = Subprocess(mock_tools)
    mock_sub._run_and_stream_output = MagicMock()
    mock_sub._subprocess.run = MagicMock()
    mock_sub._subprocess.check_output = MagicMock()
    return mock_sub


@pytest.mark.parametrize("batch_script", ["HELLO.BAT", "hello.bat", "hElLo.BaT"])
def test_run_windows_batch_script(mock_sub, batch_script):
    """Console control is released for a Windows batch script in run."""
    # Console control is only released on Windows
    mock_sub.tools.host_os = "Windows"

    with mock_sub.tools.input.wait_bar("Testing..."):
        mock_sub.run([batch_script, "World"])

    mock_sub._subprocess.run.assert_called_with(
        [batch_script, "World"],
        text=True,
        encoding=ANY,
    )
    mock_sub.tools.input.release_console_control.assert_called_once()


@pytest.mark.parametrize("batch_script", ["HELLO.BAT", "hello.bat", "hElLo.BaT"])
def test_check_output_windows_batch_script(mock_sub, batch_script):
    """Console control is released for a Windows batch script in
    check_output."""
    # Console control is only released on Windows
    mock_sub.tools.host_os = "Windows"

    with mock_sub.tools.input.wait_bar("Testing..."):
        mock_sub.check_output([batch_script, "World"])

    mock_sub._subprocess.check_output.assert_called_with(
        [batch_script, "World"],
        text=True,
        encoding=ANY,
    )
    mock_sub.tools.input.release_console_control.assert_called_once()


@pytest.mark.parametrize(
    "cmdline, kwargs",
    [
        ([], dict()),
        (["Hello", "World"], dict()),
        (["Hello", "World"], dict(val1="value1", val2="value2")),
    ],
)
def test_negative_condition_not_controlled(mock_sub, cmdline, kwargs):
    """Passthrough to Subprocess if conditions to release console control are
    not met while the console is not controlled."""
    mock_sub.run(cmdline, **kwargs)
    mock_sub._subprocess.run.assert_called_with(
        cmdline,
        **kwargs,
        text=True,
        encoding=ANY,
    )

    mock_sub.check_output(cmdline, **kwargs)
    mock_sub._subprocess.check_output.assert_called_with(
        cmdline,
        **kwargs,
        text=True,
        encoding=ANY,
    )

    mock_sub.tools.input.release_console_control.assert_not_called()


@pytest.mark.parametrize(
    "cmdline, kwargs",
    [
        ([], dict()),
        (["Hello", "World"], dict()),
        (["Hello", "World"], dict(val1="value1", val2="value2")),
    ],
)
def test_negative_condition_controlled(mock_sub, cmdline, kwargs):
    """Passthrough to Subprocess if conditions to release console control are
    not met while the console is controlled."""
    with mock_sub.tools.input.wait_bar("Testing..."):
        mock_sub.run(cmdline, **kwargs)
        mock_sub.check_output(cmdline, **kwargs)

    mock_sub._run_and_stream_output.assert_called_with(cmdline, **kwargs)
    mock_sub._subprocess.check_output.assert_called_with(
        cmdline,
        **kwargs,
        text=True,
        encoding=ANY,
    )
    mock_sub.tools.input.release_console_control.assert_not_called()
