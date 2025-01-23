import os
import subprocess
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import ANY

import pytest

from briefcase.console import LogLevel

from .conftest import CREATE_NEW_PROCESS_GROUP, CREATE_NO_WINDOW


@pytest.fixture
def caplog(mock_sub):
    # Capture the logged content independent of the console.
    actual_log = []

    def test_log(*messages, **kwargs):
        for message in messages:
            actual_log.append(message + "\n")

    mock_sub.tools.console.to_log = test_log
    return actual_log


EXPECTED_SUCCESS_OUTPUT = (
    "\n"
    ">>> Running Command:\n"
    ">>>     hello world\n"
    ">>> Working Directory:\n"
    f">>>     {Path.cwd()}\n"
    ">>> Command Output:\n"
    ">>>     some output line 1\n"
    ">>>     more output line 2\n"
    ">>> Return code: 0\n"
    "\n"
)


@pytest.mark.parametrize("platform", ["Linux", "Darwin", "Windows"])
@pytest.mark.parametrize(
    "quiet, verbosity, expected_output, expected_log",
    [
        (0, LogLevel.INFO, "", EXPECTED_SUCCESS_OUTPUT),
        (0, LogLevel.DEBUG, EXPECTED_SUCCESS_OUTPUT, EXPECTED_SUCCESS_OUTPUT),
        (1, LogLevel.INFO, "", EXPECTED_SUCCESS_OUTPUT),
        (1, LogLevel.DEBUG, EXPECTED_SUCCESS_OUTPUT, EXPECTED_SUCCESS_OUTPUT),
        (2, LogLevel.INFO, "", ""),
        (2, LogLevel.DEBUG, "", ""),
    ],
)
def test_call(
    mock_sub,
    capsys,
    caplog,
    platform,
    quiet,
    verbosity,
    expected_output,
    expected_log,
    sub_check_output_kw,
):
    """A simple call will be invoked."""
    mock_sub.tools.console.verbosity = verbosity

    mock_sub.tools.host_os = platform
    mock_sub.check_output(["hello", "world"], quiet=quiet)

    mock_sub._subprocess.check_output.assert_called_with(
        ["hello", "world"], **sub_check_output_kw
    )
    assert capsys.readouterr().out == expected_output
    assert "".join(caplog) == expected_log


def test_call_with_arg(mock_sub, capsys, sub_check_output_kw):
    """Any extra keyword arguments are passed through as-is."""

    mock_sub.check_output(["hello", "world"], extra_kw="extra")

    mock_sub._subprocess.check_output.assert_called_with(
        ["hello", "world"],
        extra_kw="extra",
        **sub_check_output_kw,
    )
    assert capsys.readouterr().out == ""


def test_call_with_path_arg(mock_sub, capsys, tmp_path, sub_check_output_kw):
    """Path-based arguments are converted to strings and passed in as-is."""

    mock_sub.check_output(["hello", tmp_path / "location"], cwd=tmp_path / "cwd")

    mock_sub._subprocess.check_output.assert_called_with(
        ["hello", os.fsdecode(tmp_path / "location")],
        cwd=os.fsdecode(tmp_path / "cwd"),
        **sub_check_output_kw,
    )
    assert capsys.readouterr().out == ""


def test_call_with_escaped_arg(mock_sub, capsys, caplog):
    """If the command contains special characters, they are shell escaped in output."""
    mock_sub.tools.console.verbosity = LogLevel.INFO

    called_process_error = CalledProcessError(
        returncode=-1,
        cmd=["hello", "my world"],
        output="output line 1\noutput line 2\n",
        stderr="error line 1\nerror line 2\n",
    )
    mock_sub._subprocess.check_output.side_effect = called_process_error

    with pytest.raises(CalledProcessError):
        mock_sub.check_output(["hello", "my world"])

    assert capsys.readouterr().out == (
        "\n"
        "Running Command:\n"
        "    hello 'my world'\n"
        "Command Output:\n"
        "    output line 1\n"
        "    output line 2\n"
        "Command Error Output (stderr):\n"
        "    error line 1\n"
        "    error line 2\n"
        "Return code: -1\n"
        "\n"
    )
    assert "".join(caplog) == (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello 'my world'\n"
        ">>> Working Directory:\n"
        f">>>     {Path.cwd()}\n"
        ">>> Command Output:\n"
        ">>>     output line 1\n"
        ">>>     output line 2\n"
        ">>> Command Error Output (stderr):\n"
        ">>>     error line 1\n"
        ">>>     error line 2\n"
        ">>> Return code: -1\n"
        "\n"
    )


@pytest.mark.parametrize(
    ("platform", "start_new_session", "check_output_kwargs"),
    [
        ("Linux", None, {}),
        ("Linux", True, {}),
        ("Linux", False, {}),
        ("Darwin", None, {}),
        ("Darwin", True, {}),
        ("Darwin", False, {}),
        ("Windows", None, {}),
        (
            "Windows",
            True,
            {"creationflags": CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW},
        ),
        ("Windows", False, {}),
    ],
)
def test_call_with_start_new_session(
    mock_sub,
    capsys,
    platform,
    start_new_session,
    check_output_kwargs,
    sub_check_output_kw,
):
    """start_new_session is passed thru on Linux and macOS but converted for Windows."""

    mock_sub.tools.host_os = platform
    mock_sub.check_output(["hello", "world"], start_new_session=start_new_session)

    final_kwargs = {**check_output_kwargs, **sub_check_output_kw}

    if platform == "Windows":
        mock_sub._subprocess.check_output.assert_called_with(
            ["hello", "world"],
            **final_kwargs,
        )
        assert capsys.readouterr().out == ""
    else:
        mock_sub._subprocess.check_output.assert_called_with(
            ["hello", "world"],
            start_new_session=start_new_session,
            **final_kwargs,
        )
        assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("creationflags", "final_creationflags"),
    [
        (0x1, CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW | 1),
        (CREATE_NEW_PROCESS_GROUP, CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW),
        (0, CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW),
    ],
)
def test_call_windows_with_start_new_session_and_creationflags(
    mock_sub,
    capsys,
    creationflags,
    final_creationflags,
):
    """Creationflags used to simulate start_new_session=True should be merged with any
    existing flags."""

    mock_sub.tools.host_os = "Windows"

    # use commented test below when merging creationflags is allowed
    with pytest.raises(
        AssertionError, match="Subprocess called with creationflags set"
    ):
        mock_sub.check_output(
            ["hello", "world"],
            start_new_session=True,
            creationflags=creationflags,
        )


def test_debug_call_with_env(mock_sub, capsys, tmp_path, sub_check_output_kw):
    """If verbosity is turned up, injected env vars are included in output."""
    mock_sub.tools.console.verbosity = LogLevel.DEBUG

    env = {"NewVar": "NewVarValue"}
    mock_sub.check_output(["hello", "world"], env=env, cwd=tmp_path / "cwd")

    merged_env = mock_sub.tools.os.environ.copy()
    merged_env.update(env)

    mock_sub._subprocess.check_output.assert_called_with(
        ["hello", "world"],
        env=merged_env,
        cwd=os.fsdecode(tmp_path / "cwd"),
        **sub_check_output_kw,
    )

    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Working Directory:\n"
        f">>>     {tmp_path / 'cwd'}\n"
        ">>> Environment Overrides:\n"
        ">>>     NewVar=NewVarValue\n"
        ">>> Command Output:\n"
        ">>>     some output line 1\n"
        ">>>     more output line 2\n"
        ">>> Return code: 0\n"
        "\n"
    )

    assert capsys.readouterr().out == expected_output


def test_debug_call_with_stderr(mock_sub, capsys, tmp_path, sub_check_output_kw):
    """If stderr is specified, it is not defaulted to stdout."""
    mock_sub.tools.console.verbosity = LogLevel.DEBUG

    mock_sub.check_output(
        ["hello", "world"],
        cwd=tmp_path / "cwd",
        stderr=subprocess.DEVNULL,
    )

    sub_check_output_kw.pop("stderr")
    mock_sub._subprocess.check_output.assert_called_with(
        ["hello", "world"],
        cwd=os.fsdecode(tmp_path / "cwd"),
        stderr=subprocess.DEVNULL,
        **sub_check_output_kw,
    )

    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Working Directory:\n"
        f">>>     {tmp_path / 'cwd'}\n"
        ">>> Command Output:\n"
        ">>>     some output line 1\n"
        ">>>     more output line 2\n"
        ">>> Return code: 0\n"
        "\n"
    )

    assert capsys.readouterr().out == expected_output


EXPECTED_ERROR_OUTPUT = (
    "\n"
    "Running Command:\n"
    "    hello world\n"
    "Command Output:\n"
    "    output line 1\n"
    "    output line 2\n"
    "Command Error Output (stderr):\n"
    "    error line 1\n"
    "    error line 2\n"
    "Return code: -1\n"
    "\n"
)
EXPECTED_ERROR_LOG_OUTPUT = (
    "\n"
    ">>> Running Command:\n"
    ">>>     hello world\n"
    ">>> Working Directory:\n"
    f">>>     {Path.cwd()}\n"
    ">>> Command Output:\n"
    ">>>     output line 1\n"
    ">>>     output line 2\n"
    ">>> Command Error Output (stderr):\n"
    ">>>     error line 1\n"
    ">>>     error line 2\n"
    ">>> Return code: -1\n"
    "\n"
)


@pytest.mark.parametrize(
    "quiet, verbosity, expected_output, expected_log",
    [
        (0, LogLevel.INFO, EXPECTED_ERROR_OUTPUT, EXPECTED_ERROR_LOG_OUTPUT),
        (0, LogLevel.DEBUG, EXPECTED_ERROR_LOG_OUTPUT, EXPECTED_ERROR_LOG_OUTPUT),
        (1, LogLevel.INFO, "", EXPECTED_ERROR_LOG_OUTPUT),
        (1, LogLevel.DEBUG, EXPECTED_ERROR_LOG_OUTPUT, EXPECTED_ERROR_LOG_OUTPUT),
        (2, LogLevel.INFO, "", ""),
        (2, LogLevel.DEBUG, "", ""),
    ],
)
def test_calledprocesserror_exception_logging(
    mock_sub,
    capsys,
    caplog,
    quiet,
    verbosity,
    expected_output,
    expected_log,
):
    """If command errors, command output is handled appropriately."""
    mock_sub.tools.console.verbosity = verbosity

    called_process_error = CalledProcessError(
        returncode=-1,
        cmd=["hello", "world"],
        output="output line 1\noutput line 2\n",
        stderr="error line 1\nerror line 2\n",
    )
    mock_sub._subprocess.check_output.side_effect = called_process_error

    with pytest.raises(CalledProcessError):
        mock_sub.check_output(["hello", "world"], quiet=quiet)

    assert capsys.readouterr().out == expected_output
    assert "".join(caplog) == expected_log


def test_calledprocesserror_exception_logging_no_output(mock_sub, capsys, caplog):
    """If command errors, and there is no command output, return code is still printed."""
    called_process_error = CalledProcessError(
        returncode=-1,
        cmd=["hello", "world"],
        output=None,
        stderr=None,
    )
    mock_sub._subprocess.check_output.side_effect = called_process_error

    with pytest.raises(CalledProcessError):
        mock_sub.check_output(["hello", "world"])

    assert capsys.readouterr().out == (
        "\n" "Running Command:\n" "    hello world\n" "Return code: -1\n" "\n"
    )
    assert "".join(caplog) == (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Working Directory:\n"
        f">>>     {Path.cwd()}\n"
        ">>> Return code: -1\n"
        "\n"
    )


@pytest.mark.parametrize(
    "in_kwargs, kwargs",
    [
        (
            {},
            {
                "text": True,
                "encoding": ANY,
                "stderr": subprocess.STDOUT,
                "errors": "backslashreplace",
            },
        ),
        (
            {"text": True},
            {
                "text": True,
                "encoding": ANY,
                "stderr": subprocess.STDOUT,
                "errors": "backslashreplace",
            },
        ),
        ({"text": False}, {"text": False, "stderr": subprocess.STDOUT}),
        (
            {"universal_newlines": False},
            {"text": False, "stderr": subprocess.STDOUT},
        ),
        (
            {"universal_newlines": True},
            {
                "text": True,
                "encoding": ANY,
                "stderr": subprocess.STDOUT,
                "errors": "backslashreplace",
            },
        ),
    ],
)
def test_text_eq_true_default_overriding(mock_sub, in_kwargs, kwargs):
    """If text or universal_newlines is explicitly provided, those should override
    text=true default and universal_newlines should be converted to text."""
    mock_sub.check_output(["hello", "world"], stderr=subprocess.STDOUT, **in_kwargs)

    mock_sub._subprocess.check_output.assert_called_with(["hello", "world"], **kwargs)
