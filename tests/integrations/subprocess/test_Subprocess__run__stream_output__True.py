import os
import subprocess
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import ANY

import pytest

from briefcase.console import LogLevel

from .conftest import CREATE_NEW_PROCESS_GROUP, CREATE_NO_WINDOW


@pytest.mark.parametrize("platform", ["Linux", "Darwin", "Windows"])
def test_call(mock_sub, capsys, platform, sub_stream_kw, sleep_zero):
    """A simple call will be invoked."""

    mock_sub.tools.sys.platform = platform
    mock_sub.run(["hello", "world"])

    mock_sub._subprocess.Popen.assert_called_with(["hello", "world"], **sub_stream_kw)
    # fmt: off
    expected_output = (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output


def test_call_with_arg(mock_sub, capsys, sub_stream_kw, sleep_zero):
    """Any extra keyword arguments are passed through as-is."""

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
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output


def test_call_with_path_arg(mock_sub, capsys, tmp_path, sub_stream_kw, sleep_zero):
    """Path-based arguments are converted to strings and passed in as-is."""

    mock_sub.run(["hello", tmp_path / "location"], cwd=tmp_path / "cwd")

    mock_sub._subprocess.Popen.assert_called_with(
        ["hello", os.fsdecode(tmp_path / "location")],
        cwd=os.fsdecode(tmp_path / "cwd"),
        **sub_stream_kw,
    )
    # fmt: off
    expected_output = (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output


@pytest.mark.parametrize(
    ("platform", "start_new_session", "run_kwargs"),
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
    run_kwargs,
    sub_stream_kw,
    sleep_zero,
):
    """start_new_session is passed thru on Linux and macOS but converted for Windows."""

    mock_sub.tools.host_os = platform
    mock_sub.run(["hello", "world"], start_new_session=start_new_session)

    final_kwargs = {**sub_stream_kw, **run_kwargs}
    if platform == "Windows":
        mock_sub._subprocess.Popen.assert_called_with(
            ["hello", "world"],
            **final_kwargs,
        )
    else:
        mock_sub._subprocess.Popen.assert_called_with(
            ["hello", "world"],
            start_new_session=start_new_session,
            **final_kwargs,
        )

    # fmt: off
    expected_output = (
        "output line 1\n"
        "\n"
        "output line 3\n"
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output


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
    sleep_zero,
):
    """Creationflags used to simulate start_new_session=True should be merged with any
    existing flags."""

    mock_sub.tools.host_os = "Windows"

    # use commented test below when merging creationflags is allowed
    with pytest.raises(
        AssertionError,
        match="Subprocess called with creationflags set",
    ):
        mock_sub.run(
            ["hello", "world"],
            start_new_session=True,
            creationflags=creationflags,
        )


def test_debug_call(mock_sub, capsys, sub_stream_kw, sleep_zero):
    """If verbosity is turned up, there is output."""
    mock_sub.tools.logger.verbosity = LogLevel.DEBUG

    mock_sub.run(["hello", "world"])

    mock_sub._subprocess.Popen.assert_called_with(["hello", "world"], **sub_stream_kw)
    # fmt: off
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
    )
    # fmt: on

    assert capsys.readouterr().out == expected_output


def test_debug_call_with_env(mock_sub, capsys, tmp_path, sub_stream_kw, sleep_zero):
    """If verbosity is turned up, injected env vars are included output."""
    mock_sub.tools.logger.verbosity = LogLevel.DEBUG

    env = {"NewVar": "NewVarValue"}
    mock_sub.run(["hello", "world"], env=env, cwd=tmp_path / "cwd")

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
    )
    assert capsys.readouterr().out == expected_output


def test_calledprocesserror_exception_logging(mock_sub, sleep_zero, capsys):
    mock_sub.tools.logger.verbosity = LogLevel.DEBUG

    with pytest.raises(CalledProcessError):
        mock_sub.run(["hello", "world"], check=True)

    # fmt: off
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
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output


@pytest.mark.parametrize(
    "in_kwargs, kwargs",
    [
        ({}, {"text": True, "encoding": ANY, "errors": "backslashreplace"}),
        ({"text": True}, {"text": True, "encoding": ANY, "errors": "backslashreplace"}),
        ({"text": False}, {"text": False}),
        ({"universal_newlines": False}, {"text": False}),
        (
            {"universal_newlines": True},
            {"text": True, "encoding": ANY, "errors": "backslashreplace"},
        ),
    ],
)
def test_text_eq_true_default_overriding(mock_sub, in_kwargs, kwargs, sleep_zero):
    """If text or universal_newlines is explicitly provided, those should override
    text=true default and universal_newlines should be converted to text."""
    mock_sub.run(["hello", "world"], **in_kwargs)

    mock_sub._subprocess.Popen.assert_called_with(
        ["hello", "world"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        **kwargs,
    )


@pytest.mark.parametrize("platform", ["Linux", "Darwin", "Windows"])
def test_filtered_output(mock_sub, capsys, platform, sub_stream_kw, sleep_zero):
    """Streamed output can be filtered."""

    # Add an output filter that replaces all spaces with newlines.
    def space_filter(line):
        yield from line.split(" ")

    mock_sub.tools.sys.platform = platform
    mock_sub.run(
        ["hello", "world"],
        filter_func=space_filter,
    )

    mock_sub._subprocess.Popen.assert_called_with(
        ["hello", "world"],
        **sub_stream_kw,
    )
    # fmt: off
    expected_output = (
        "output\n"
        "line\n"
        "1\n"
        "\n"
        "output\n"
        "line\n"
        "3\n"
    )
    # fmt: on
    assert capsys.readouterr().out == expected_output
