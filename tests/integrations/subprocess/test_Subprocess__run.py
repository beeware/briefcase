import os
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import ANY

import pytest

from .conftest import CREATE_NEW_PROCESS_GROUP, CREATE_NO_WINDOW


@pytest.mark.parametrize("platform", ["Linux", "Darwin", "Windows"])
def test_call(mock_sub, capsys, platform):
    """A simple call will be invoked."""

    mock_sub.tools.sys.platform = platform
    mock_sub.run(["hello", "world"])

    mock_sub._subprocess.run.assert_called_with(
        ["hello", "world"],
        text=True,
        encoding=ANY,
    )
    assert capsys.readouterr().out == ""


def test_call_with_arg(mock_sub, capsys):
    """Any extra keyword arguments are passed through as-is."""

    mock_sub.run(["hello", "world"], universal_newlines=True)

    mock_sub._subprocess.run.assert_called_with(
        ["hello", "world"],
        universal_newlines=True,
        encoding=ANY,
    )
    assert capsys.readouterr().out == ""


def test_call_with_path_arg(mock_sub, capsys, tmp_path):
    """Path-based arguments are converted to strings and passed in as-is."""

    mock_sub.run(["hello", tmp_path / "location"], cwd=tmp_path / "cwd")

    mock_sub._subprocess.run.assert_called_with(
        ["hello", os.fsdecode(tmp_path / "location")],
        cwd=os.fsdecode(tmp_path / "cwd"),
        text=True,
        encoding=ANY,
    )
    assert capsys.readouterr().out == ""


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
):
    """start_new_session is passed thru on Linux and macOS but converted for
    Windows."""

    mock_sub.tools.host_os = platform
    mock_sub.run(["hello", "world"], start_new_session=start_new_session)

    if platform == "Windows":
        mock_sub._subprocess.run.assert_called_with(
            ["hello", "world"],
            text=True,
            encoding=ANY,
            **run_kwargs,
        )
        assert capsys.readouterr().out == ""
    else:
        mock_sub._subprocess.run.assert_called_with(
            ["hello", "world"],
            start_new_session=start_new_session,
            text=True,
            encoding=ANY,
            **run_kwargs,
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
    """creationflags used to simulate start_new_session=True should be merged
    with any existing flags."""

    mock_sub.tools.host_os = "Windows"

    # use commented test below when merging creationflags is allowed
    with pytest.raises(
        AssertionError, match="Subprocess called with creationflags set"
    ):
        mock_sub.run(
            ["hello", "world"], start_new_session=True, creationflags=creationflags
        )


def test_debug_call(mock_sub, capsys):
    """If verbosity is turned up, there is output."""
    mock_sub.tools.logger.verbosity = 2

    mock_sub.run(["hello", "world"])

    mock_sub._subprocess.run.assert_called_with(
        ["hello", "world"],
        text=True,
        encoding=ANY,
    )
    # fmt: off
    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Working Directory:\n"
        f">>>     {Path.cwd()}\n"
        ">>> Return code: 0\n"
    )
    # fmt: on

    assert capsys.readouterr().out == expected_output


def test_debug_call_with_env(mock_sub, capsys, tmp_path):
    """If verbosity is turned up, injected env vars are included output."""
    mock_sub.tools.logger.verbosity = 2

    env = {"NewVar": "NewVarValue"}
    mock_sub.run(["hello", "world"], env=env, cwd=tmp_path / "cwd")

    merged_env = mock_sub.tools.os.environ.copy()
    merged_env.update(env)

    mock_sub._subprocess.run.assert_called_with(
        ["hello", "world"],
        env=merged_env,
        cwd=os.fsdecode(tmp_path / "cwd"),
        text=True,
        encoding=ANY,
    )
    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Working Directory:\n"
        f">>>     {tmp_path / 'cwd'}\n"
        ">>> Environment Overrides:\n"
        ">>>     NewVar=NewVarValue\n"
        ">>> Return code: 0\n"
    )
    assert capsys.readouterr().out == expected_output


def test_calledprocesserror_exception_logging(mock_sub, capsys):
    mock_sub.tools.logger.verbosity = 2

    called_process_error = CalledProcessError(
        returncode=-1,
        cmd="hello world",
        output="output line 1\noutput line 2",
        stderr="error line 1\nerror line 2",
    )
    mock_sub._subprocess.run.side_effect = called_process_error

    with pytest.raises(CalledProcessError):
        mock_sub.run(["hello", "world"])

    # fmt: off
    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Working Directory:\n"
        f">>>     {Path.cwd()}\n"
        ">>> Return code: -1\n"
    )
    # fmt: on

    assert capsys.readouterr().out == expected_output


@pytest.mark.parametrize(
    "in_kwargs, kwargs",
    [
        ({}, {"text": True, "encoding": ANY}),
        ({"text": True}, {"text": True, "encoding": ANY}),
        ({"text": False}, {"text": False}),
        ({"universal_newlines": False}, {"universal_newlines": False}),
        ({"universal_newlines": True}, {"universal_newlines": True, "encoding": ANY}),
    ],
)
def test_text_eq_true_default_overriding(mock_sub, in_kwargs, kwargs):
    """if text or universal_newlines is explicitly provided, those should
    override text=true default."""

    mock_sub.run(["hello", "world"], **in_kwargs)
    mock_sub._subprocess.run.assert_called_with(["hello", "world"], **kwargs)
