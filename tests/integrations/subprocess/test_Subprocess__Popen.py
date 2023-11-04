import os
from pathlib import Path
from unittest.mock import ANY

import pytest

from briefcase.console import LogLevel

from .conftest import CREATE_NEW_PROCESS_GROUP, CREATE_NO_WINDOW


@pytest.mark.parametrize("platform", ["Linux", "Darwin", "Windows"])
def test_call(mock_sub, capsys, platform, sub_kw):
    """A simple call will be invoked."""

    mock_sub.tools.host_os = platform
    mock_sub.Popen(["hello", "world"])

    mock_sub._subprocess.Popen.assert_called_with(["hello", "world"], **sub_kw)
    assert capsys.readouterr().out == ""


def test_call_with_arg(mock_sub, capsys, sub_kw):
    """Any extra keyword arguments are passed through as-is."""

    mock_sub.Popen(["hello", "world"], extra_kw="extra")

    mock_sub._subprocess.Popen.assert_called_with(
        ["hello", "world"],
        extra_kw="extra",
        **sub_kw,
    )
    assert capsys.readouterr().out == ""


def test_call_with_path_arg(mock_sub, capsys, tmp_path, sub_kw):
    """Path-based arguments are converted to strings and passed in as-is."""

    mock_sub.Popen(["hello", tmp_path / "location"], cwd=tmp_path / "cwd")

    mock_sub._subprocess.Popen.assert_called_with(
        ["hello", os.fsdecode(tmp_path / "location")],
        cwd=os.fsdecode(tmp_path / "cwd"),
        **sub_kw,
    )
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("platform", "start_new_session", "popen_kwargs"),
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
    popen_kwargs,
    sub_kw,
):
    """start_new_session is passed thru on Linux and macOS but converted for Windows."""

    mock_sub.tools.host_os = platform
    mock_sub.Popen(["hello", "world"], start_new_session=start_new_session)

    final_kwargs = {**sub_kw, **popen_kwargs}
    if platform == "Windows":
        mock_sub._subprocess.Popen.assert_called_with(
            ["hello", "world"], **final_kwargs
        )
        assert capsys.readouterr().out == ""
    else:
        mock_sub._subprocess.Popen.assert_called_with(
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
        mock_sub.Popen(
            ["hello", "world"],
            start_new_session=True,
            creationflags=creationflags,
        )


def test_debug_call(mock_sub, capsys, sub_kw):
    """If verbosity is turned up, there is output."""
    mock_sub.tools.logger.verbosity = LogLevel.DEBUG
    mock_sub.Popen(["hello", "world"])

    mock_sub._subprocess.Popen.assert_called_with(["hello", "world"], **sub_kw)

    assert capsys.readouterr().out == (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Working Directory:\n"
        f">>>     {Path.cwd()}\n"
    )


def test_debug_call_with_env(mock_sub, capsys, tmp_path, sub_kw):
    """If verbosity is turned up, and injected env vars are included output."""
    mock_sub.tools.logger.verbosity = LogLevel.DEBUG

    env = {"NewVar": "NewVarValue"}
    mock_sub.Popen(["hello", "world"], env=env, cwd=tmp_path / "cwd")

    merged_env = mock_sub.tools.os.environ.copy()
    merged_env.update(env)

    mock_sub._subprocess.Popen.assert_called_with(
        ["hello", "world"],
        env=merged_env,
        cwd=os.fsdecode(tmp_path / "cwd"),
        **sub_kw,
    )

    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Working Directory:\n"
        f">>>     {tmp_path / 'cwd'}\n"
        ">>> Environment Overrides:\n"
        ">>>     NewVar=NewVarValue\n"
    )
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
def test_text_eq_true_default_overriding(mock_sub, in_kwargs, kwargs):
    """If text or universal_newlines is explicitly provided, those should override
    text=true default and universal_newlines should be converted to text."""

    mock_sub.Popen(["hello", "world"], **in_kwargs)
    mock_sub._subprocess.Popen.assert_called_with(["hello", "world"], **kwargs)
