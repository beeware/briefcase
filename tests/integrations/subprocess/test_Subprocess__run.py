import os
from subprocess import CalledProcessError

import pytest

from briefcase.console import Log

from .conftest import CREATE_NEW_PROCESS_GROUP, CREATE_NO_WINDOW


@pytest.mark.parametrize("platform", ["Linux", "Darwin", "Windows"])
def test_call(mock_sub, capsys, platform):
    """A simple call will be invoked."""

    mock_sub.command.sys.platform = platform
    mock_sub.run(["hello", "world"])

    mock_sub._subprocess.run.assert_called_with(["hello", "world"], text=True)
    assert capsys.readouterr().out == ""


def test_call_with_arg(mock_sub, capsys):
    """Any extra keyword arguments are passed through as-is."""

    mock_sub.run(["hello", "world"], universal_newlines=True)

    mock_sub._subprocess.run.assert_called_with(
        ["hello", "world"], universal_newlines=True
    )
    assert capsys.readouterr().out == ""


def test_call_with_path_arg(mock_sub, capsys, tmp_path):
    """Path-based arguments are converted to strings andpassed in as-is."""

    mock_sub.run(["hello", tmp_path / "location"], cwd=tmp_path / "cwd")

    mock_sub._subprocess.run.assert_called_with(
        ["hello", os.fsdecode(tmp_path / "location")],
        cwd=os.fsdecode(tmp_path / "cwd"),
        text=True,
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
    mock_sub, capsys, platform, start_new_session, run_kwargs
):
    """start_new_session is passed thru on Linux and macOS but converted for
    Windows."""

    mock_sub.command.host_os = platform
    mock_sub.run(["hello", "world"], start_new_session=start_new_session)

    if platform == "Windows":
        mock_sub._subprocess.run.assert_called_with(
            ["hello", "world"],
            text=True,
            **run_kwargs,
        )
        assert capsys.readouterr().out == ""
    else:
        mock_sub._subprocess.run.assert_called_with(
            ["hello", "world"],
            start_new_session=start_new_session,
            text=True,
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
    mock_sub, capsys, creationflags, final_creationflags
):
    """creationflags used to simulate start_new_session=True should be merged
    with any existing flags."""

    mock_sub.command.host_os = "Windows"

    # use commented test below when merging creationflags is allowed
    with pytest.raises(
        AssertionError, match="Subprocess called with creationflags set"
    ):
        mock_sub.run(
            ["hello", "world"], start_new_session=True, creationflags=creationflags
        )


def test_debug_call(mock_sub, capsys):
    """If verbosity is turned up, there is output."""
    mock_sub.command.logger = Log(verbosity=2)

    mock_sub.run(["hello", "world"])

    mock_sub._subprocess.run.assert_called_with(["hello", "world"], text=True)
    assert capsys.readouterr().out == (
        "\n" ">>> Running Command:\n" ">>>     hello world\n"
    )


def test_debug_call_with_env(mock_sub, capsys):
    """If verbosity is turned up, injected env vars are included output."""
    mock_sub.command.logger = Log(verbosity=2)

    env = {"NewVar": "NewVarValue"}
    mock_sub.run(["hello", "world"], env=env)

    merged_env = mock_sub.command.os.environ.copy()
    merged_env.update(env)

    mock_sub._subprocess.run.assert_called_with(
        ["hello", "world"], env=merged_env, text=True
    )

    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Environment:\n"
        ">>>     NewVar=NewVarValue\n"
    )

    assert capsys.readouterr().out == expected_output


def test_deep_debug_call(mock_sub, capsys):
    """If verbosity is at the max, the full environment and return is
    output."""
    mock_sub.command.logger = Log(verbosity=3)

    mock_sub.run(["hello", "world"])

    mock_sub._subprocess.run.assert_called_with(["hello", "world"], text=True)

    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Full Environment:\n"
        ">>>     VAR1=Value 1\n"
        ">>>     PS1=\n"
        ">>> Line 2\n"
        ">>> \n"
        ">>> Line 4\n"
        ">>>     PWD=/home/user/\n"
        ">>> Return code: 0\n"
    )

    assert capsys.readouterr().out == expected_output


def test_deep_debug_call_with_env(mock_sub, capsys):
    """If verbosity is at the max, the full environment and return is output,
    and the environment is merged."""
    mock_sub.command.logger = Log(verbosity=3)

    env = {"NewVar": "NewVarValue"}
    mock_sub.run(["hello", "world"], env=env)

    merged_env = mock_sub.command.os.environ.copy()
    merged_env.update(env)

    mock_sub._subprocess.run.assert_called_with(
        ["hello", "world"], env=merged_env, text=True
    )

    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Full Environment:\n"
        ">>>     VAR1=Value 1\n"
        ">>>     PS1=\n"
        ">>> Line 2\n"
        ">>> \n"
        ">>> Line 4\n"
        ">>>     PWD=/home/user/\n"
        ">>>     NewVar=NewVarValue\n"
        ">>> Return code: 0\n"
    )

    assert capsys.readouterr().out == expected_output


def test_calledprocesserror_exception_logging(mock_sub, capsys):
    mock_sub.command.logger = Log(verbosity=3)

    called_process_error = CalledProcessError(
        returncode=-1,
        cmd="hello world",
        output="output line 1\noutput line 2",
        stderr="error line 1\nerror line 2",
    )
    mock_sub._subprocess.run.side_effect = called_process_error

    with pytest.raises(CalledProcessError):
        mock_sub.run(["hello", "world"])

    expected_output = (
        "\n"
        ">>> Running Command:\n"
        ">>>     hello world\n"
        ">>> Full Environment:\n"
        ">>>     VAR1=Value 1\n"
        ">>>     PS1=\n"
        ">>> Line 2\n"
        ">>> \n"
        ">>> Line 4\n"
        ">>>     PWD=/home/user/\n"
        ">>> Return code: -1\n"
    )

    assert capsys.readouterr().out == expected_output


@pytest.mark.parametrize(
    "in_kwargs, kwargs",
    [
        ({}, {"text": True}),
        ({"text": True}, {"text": True}),
        ({"text": False}, {"text": False}),
        ({"universal_newlines": False}, {"universal_newlines": False}),
        ({"universal_newlines": True}, {"universal_newlines": True}),
    ],
)
def test_text_eq_true_default_overriding(mock_sub, in_kwargs, kwargs):
    """if text or universal_newlines is explicitly provided, those should
    override text=true default."""

    mock_sub.run(["hello", "world"], **in_kwargs)
    mock_sub._subprocess.run.assert_called_with(["hello", "world"], **kwargs)
