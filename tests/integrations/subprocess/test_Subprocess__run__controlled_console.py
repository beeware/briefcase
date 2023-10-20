import os
import subprocess
from pathlib import Path
from unittest.mock import ANY

import pytest

from briefcase.console import LogLevel


def test_call(mock_sub, sub_stream_kw, sleep_zero, capsys):
    """A simple call will be invoked."""

    with mock_sub.tools.input.wait_bar():
        mock_sub.run(["hello", "world"])

    mock_sub._subprocess.Popen.assert_called_with(["hello", "world"], **sub_stream_kw)
    # fmt: off
    expected_output = (
        "output line 1\n"
        "\n"
        "output line 3\n"
        "\n"
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output


def test_call_with_arg(mock_sub, sub_stream_kw, sleep_zero, capsys):
    """Any extra keyword arguments are passed through as-is."""

    with mock_sub.tools.input.wait_bar():
        mock_sub.run(["hello", "world"], extra_kw="extra")

    mock_sub._subprocess.Popen.assert_called_with(
        ["hello", "world"],
        extra_kw="extra",
        **sub_stream_kw,
    )
    # fmt: off
    expected_output = (
        "output line 1\n"
        "\n"
        "output line 3\n"
        "\n"
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output


def test_debug_call(mock_sub, sub_stream_kw, sleep_zero, capsys):
    """If verbosity is turned up, there is debug output."""
    mock_sub.tools.logger.verbosity = LogLevel.DEBUG

    with mock_sub.tools.input.wait_bar():
        mock_sub.run(["hello", "world"])

    mock_sub._subprocess.Popen.assert_called_with(["hello", "world"], **sub_stream_kw)
    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Working Directory:\n"
        f">>>     {Path.cwd()}\n"
        "output line 1\n"
        "\n"
        "output line 3\n"
        ">>> Return code: -3\n"
        "\n"
    )
    assert capsys.readouterr().out == expected_output


def test_debug_call_with_env(mock_sub, sub_stream_kw, sleep_zero, capsys, tmp_path):
    """If verbosity is turned up, injected env vars are included in debug output."""
    mock_sub.tools.logger.verbosity = LogLevel.DEBUG

    env = {"NewVar": "NewVarValue"}
    with mock_sub.tools.input.wait_bar():
        mock_sub.run(
            ["hello", "world"],
            env=env,
            cwd=tmp_path / "cwd",
        )

    merged_env = mock_sub.tools.os.environ.copy()
    merged_env.update(env)

    mock_sub._subprocess.Popen.assert_called_with(
        ["hello", "world"],
        env=merged_env,
        cwd=os.fsdecode(tmp_path / "cwd"),
        **sub_stream_kw,
    )
    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Working Directory:\n"
        f">>>     {tmp_path / 'cwd'}\n"
        ">>> Environment Overrides:\n"
        ">>>     NewVar=NewVarValue\n"
        "output line 1\n"
        "\n"
        "output line 3\n"
        ">>> Return code: -3\n"
        "\n"
    )
    assert capsys.readouterr().out == expected_output


@pytest.mark.parametrize(
    "in_kwargs, kwargs",
    [
        (
            {},
            {"text": True, "encoding": ANY, "bufsize": 1, "errors": "backslashreplace"},
        ),
        (
            {"text": True},
            {"text": True, "encoding": ANY, "bufsize": 1, "errors": "backslashreplace"},
        ),
        ({"text": False}, {"text": False, "bufsize": 1}),
        ({"text": False, "bufsize": 42}, {"text": False, "bufsize": 42}),
        ({"universal_newlines": False}, {"text": False, "bufsize": 1}),
        (
            {"universal_newlines": True},
            {"text": True, "encoding": ANY, "bufsize": 1, "errors": "backslashreplace"},
        ),
    ],
)
def test_text_eq_true_default_overriding(mock_sub, in_kwargs, kwargs, sleep_zero):
    """If text or universal_newlines is explicitly provided, those should override
    text=true default and universal_newlines should be converted to text."""
    with mock_sub.tools.input.wait_bar():
        mock_sub.run(["hello", "world"], **in_kwargs)

    mock_sub._subprocess.Popen.assert_called_with(
        ["hello", "world"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **kwargs,
    )


def test_stderr_is_redirected(
    mock_sub,
    streaming_process,
    sub_stream_kw,
    sleep_zero,
    capsys,
):
    """When stderr is redirected, it should be included in the result."""
    stderr_output = "stderr output\nline 2"
    streaming_process.stderr.read.return_value = stderr_output

    with mock_sub.tools.input.wait_bar():
        run_result = mock_sub.run(
            ["hello", "world"],
            stderr=subprocess.PIPE,
        )

    sub_stream_kw.pop("stderr")
    mock_sub._subprocess.Popen.assert_called_with(
        ["hello", "world"],
        stderr=subprocess.PIPE,
        **sub_stream_kw,
    )
    # fmt: off
    expected_output = (
        "output line 1\n"
        "\n"
        "output line 3\n"
        "\n"
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output
    assert run_result.stderr == stderr_output


def test_stderr_dev_null(
    mock_sub,
    streaming_process,
    sub_stream_kw,
    sleep_zero,
    capsys,
):
    """When stderr is discarded, it should be None in the result."""
    streaming_process.stderr = None

    with mock_sub.tools.input.wait_bar():
        run_result = mock_sub.run(
            ["hello", "world"],
            stderr=subprocess.DEVNULL,
        )

    sub_stream_kw.pop("stderr")
    mock_sub._subprocess.Popen.assert_called_with(
        ["hello", "world"],
        stderr=subprocess.DEVNULL,
        **sub_stream_kw,
    )
    # fmt: off
    expected_output = (
        "output line 1\n"
        "\n"
        "output line 3\n"
        "\n"
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output
    assert run_result.stderr is None


def test_calledprocesserror(mock_sub, streaming_process, sleep_zero, capsys):
    """CalledProcessError is raised with check=True and non-zero return value."""
    stderr_output = "stderr output\nline 2"
    streaming_process.stderr.read.return_value = stderr_output

    with pytest.raises(subprocess.CalledProcessError) as exc:
        with mock_sub.tools.input.wait_bar():
            mock_sub.run(
                ["hello", "world"],
                check=True,
                stderr=subprocess.PIPE,
            )

    # fmt: off
    expected_output = (
        "output line 1\n"
        "\n"
        "output line 3\n"
        "\n"
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output
    assert exc.value.returncode == -3
    assert exc.value.cmd == ["hello", "world"]
    assert exc.value.stderr == stderr_output


def test_invalid_invocations(mock_sub):
    """Ensure run cannot be used in a Wait Bar with invalid arguments."""
    with pytest.raises(AssertionError):
        with mock_sub.tools.input.wait_bar():
            mock_sub.run(
                ["hello", "world"],
                stdout=subprocess.PIPE,
            )

    for invalid_arg in ("timeout", "input"):
        with pytest.raises(AssertionError):
            with mock_sub.tools.input.wait_bar():
                mock_sub.run(["hello", "world"], **{invalid_arg: "value"})
