import subprocess
from unittest.mock import MagicMock, Mock

import pytest

from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def mock_sub(mock_tools):
    mock_tools.input.release_console_control = Mock(
        wraps=mock_tools.input.release_console_control
    )
    mock_sub = Subprocess(mock_tools)
    mock_sub._subprocess = MagicMock(spec_set=subprocess)
    mock_sub._run_and_stream_output = MagicMock()
    return mock_sub


@pytest.mark.parametrize("batch_script", ["HELLO.BAT", "hello.bat", "hElLo.BaT"])
def test_run_windows_batch_script(mock_sub, batch_script):
    """Console control is released for a Windows batch script in run."""
    # Console control is only released on Windows
    mock_sub.tools.host_os = "Windows"

    with mock_sub.tools.input.wait_bar("Testing..."):
        mock_sub.run([batch_script, "World"])

    mock_sub._run_and_stream_output.assert_called_with(
        [batch_script, "World"],
        filter_func=None,
    )
    mock_sub.tools.input.release_console_control.assert_called_once()


@pytest.mark.parametrize("batch_script", ["HELLO.BAT", "hello.bat", "hElLo.BaT"])
def test_check_output_windows_batch_script(mock_sub, batch_script, sub_check_output_kw):
    """Console control is released for a Windows batch script in check_output."""
    # Console control is only released on Windows for batch scripts
    mock_sub.tools.host_os = "Windows"

    with mock_sub.tools.input.wait_bar("Testing..."):
        mock_sub.check_output([batch_script, "World"])

    mock_sub._subprocess.check_output.assert_called_with(
        [batch_script, "World"],
        **sub_check_output_kw,
    )
    mock_sub.tools.input.release_console_control.assert_called_once()


@pytest.mark.parametrize("sub_kwargs", [{"stream_output": True}, {}])
def test_run_stream_output_true(mock_sub, sub_kwargs):
    """Console control is not released when stream_output=True or is unspecified."""
    with mock_sub.tools.input.wait_bar("Testing..."):
        mock_sub.run(["Hello", "World"], **sub_kwargs)

    mock_sub._run_and_stream_output.assert_called_with(
        ["Hello", "World"],
        filter_func=None,
    )
    mock_sub.tools.input.release_console_control.assert_not_called()


def test_run_stream_output_false(mock_sub, sub_kw):
    """Console control is released when stream_output=False."""
    with mock_sub.tools.input.wait_bar("Testing..."):
        mock_sub.run(["Hello", "World"], stream_output=False)

    mock_sub._subprocess.run.assert_called_with(["Hello", "World"], **sub_kw)
    mock_sub.tools.input.release_console_control.assert_called_once()


@pytest.mark.parametrize(
    "cmdline, kwargs",
    [
        ([], dict()),
        (["Hello", "World"], dict()),
        (["Hello", "World"], dict(val1="value1", val2="value2")),
    ],
)
def test_negative_condition_not_controlled(
    mock_sub,
    cmdline,
    sub_check_output_kw,
    kwargs,
):
    """Passthrough to Subprocess if conditions to release console control are not met
    while the console is not controlled."""
    mock_sub.run(cmdline, **kwargs)
    mock_sub._run_and_stream_output.assert_called_with(
        cmdline,
        filter_func=None,
        **kwargs,
    )

    mock_sub.check_output(cmdline, **kwargs)

    final_kwargs = {**sub_check_output_kw, **kwargs}
    mock_sub._subprocess.check_output.assert_called_with(cmdline, **final_kwargs)
    mock_sub.tools.input.release_console_control.assert_not_called()


@pytest.mark.parametrize(
    "cmdline, kwargs",
    [
        ([], dict()),
        (["Hello", "World"], dict()),
        (["Hello", "World"], dict(val1="value1", val2="value2")),
    ],
)
def test_negative_condition_controlled(mock_sub, cmdline, kwargs, sub_check_output_kw):
    """Passthrough to Subprocess if conditions to release console control are not met
    while the console is controlled."""
    with mock_sub.tools.input.wait_bar("Testing..."):
        mock_sub.run(cmdline, **kwargs)
        mock_sub.check_output(cmdline, **kwargs)

    mock_sub._run_and_stream_output.assert_called_with(
        cmdline,
        filter_func=None,
        **kwargs,
    )
    final_kwargs = {**sub_check_output_kw, **kwargs}
    mock_sub._subprocess.check_output.assert_called_with(cmdline, **final_kwargs)
    mock_sub.tools.input.release_console_control.assert_not_called()
