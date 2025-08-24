import subprocess
import sys
from unittest import mock

import pytest


def test_dev_run(dev_command, first_app, tmp_path):
    """The app can be run in dev mode."""
    dev_command._stream_app_logs = mock.MagicMock()
    app_popen = mock.MagicMock()
    dev_command.tools.subprocess.Popen.return_value = app_popen

    dev_command.run_dev_app(
        first_app,
        env={"a": 1, "b": 2, "c": 3},
        passthrough=[],
    )

    dev_command.tools.subprocess.Popen.assert_called_once_with(
        [
            sys.executable,
            "-c",
            (
                "import runpy, sys;"
                "sys.path.pop(0);"
                "sys.argv.extend([]);"
                'runpy.run_module("first", run_name="__main__", alter_sys=True)'
            ),
        ],
        env={
            "a": 1,
            "b": 2,
            "c": 3,
            "PYTHONUNBUFFERED": "1",
            "PYTHONDEVMODE": "1",
            "PYTHONUTF8": "1",
        },
        cwd=dev_command.tools.home_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        encoding="UTF-8",
    )
    dev_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=app_popen,
        clean_output=False,
    )


def test_dev_run_with_args(dev_command, first_app, tmp_path):
    "The app can be run in dev mode with arguments"
    dev_command._stream_app_logs = mock.MagicMock()
    app_popen = mock.MagicMock()
    dev_command.tools.subprocess.Popen.return_value = app_popen

    dev_command.run_dev_app(
        first_app,
        env={"a": 1, "b": 2, "c": 3},
        passthrough=["foo", "bar", "--whiz"],
    )

    dev_command.tools.subprocess.Popen.assert_called_once_with(
        [
            sys.executable,
            "-c",
            (
                "import runpy, sys;"
                "sys.path.pop(0);"
                "sys.argv.extend(['foo', 'bar', '--whiz']);"
                'runpy.run_module("first", run_name="__main__", alter_sys=True)'
            ),
        ],
        env={
            "a": 1,
            "b": 2,
            "c": 3,
            "PYTHONUNBUFFERED": "1",
            "PYTHONDEVMODE": "1",
            "PYTHONUTF8": "1",
        },
        cwd=dev_command.tools.home_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        encoding="UTF-8",
    )
    dev_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=app_popen,
        clean_output=False,
    )


@pytest.mark.parametrize("is_console_app", [True, False])
def test_dev_test_mode(dev_command, first_app, is_console_app, tmp_path):
    """The test suite can be run in development mode."""
    # Test mode is the same regardless of whether it's a console app or not.
    first_app.console_app = is_console_app
    first_app.test_mode = True

    dev_command._stream_app_logs = mock.MagicMock()
    app_popen = mock.MagicMock()
    dev_command.tools.subprocess.Popen.return_value = app_popen

    dev_command.run_dev_app(
        first_app,
        env={"a": 1, "b": 2, "c": 3},
        passthrough=[],
    )

    dev_command.tools.subprocess.Popen.assert_called_once_with(
        [
            sys.executable,
            "-c",
            (
                "import runpy, sys;"
                "sys.path.pop(0);"
                "sys.argv.extend([]);"
                'runpy.run_module("tests.first", run_name="__main__", alter_sys=True)'
            ),
        ],
        env={
            "a": 1,
            "b": 2,
            "c": 3,
            "PYTHONUNBUFFERED": "1",
            "PYTHONDEVMODE": "1",
            "PYTHONUTF8": "1",
        },
        cwd=dev_command.tools.home_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        encoding="UTF-8",
    )
    dev_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=app_popen,
        clean_output=False,
    )


@pytest.mark.parametrize("is_console_app", [True, False])
def test_dev_test_mode_with_args(dev_command, first_app, is_console_app, tmp_path):
    """The test suite can be run in development mode with args."""
    # Test mode is the same regardless of whether it's a console app or not.
    first_app.console_app = is_console_app
    first_app.test_mode = True

    dev_command._stream_app_logs = mock.MagicMock()
    app_popen = mock.MagicMock()
    dev_command.tools.subprocess.Popen.return_value = app_popen

    dev_command.run_dev_app(
        first_app,
        env={"a": 1, "b": 2, "c": 3},
        passthrough=["foo", "bar", "--whiz"],
    )

    dev_command.tools.subprocess.Popen.assert_called_once_with(
        [
            sys.executable,
            "-c",
            (
                "import runpy, sys;"
                "sys.path.pop(0);"
                "sys.argv.extend(['foo', 'bar', '--whiz']);"
                'runpy.run_module("tests.first", run_name="__main__", alter_sys=True)'
            ),
        ],
        env={
            "a": 1,
            "b": 2,
            "c": 3,
            "PYTHONUNBUFFERED": "1",
            "PYTHONDEVMODE": "1",
            "PYTHONUTF8": "1",
        },
        cwd=dev_command.tools.home_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        encoding="UTF-8",
    )
    dev_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=app_popen,
        clean_output=False,
    )


def test_dev_run_console(dev_command, first_app, tmp_path):
    """A console app can be run in dev mode."""
    # Modify the app to be a console app
    first_app.console_app = True

    dev_command._stream_app_logs = mock.MagicMock()

    dev_command.run_dev_app(
        first_app,
        env={"a": 1, "b": 2, "c": 3},
        passthrough=[],
    )

    dev_command.tools.subprocess.run.assert_called_once_with(
        [
            sys.executable,
            "-c",
            (
                "import runpy, sys;"
                "sys.path.pop(0);"
                "sys.argv.extend([]);"
                'runpy.run_module("first", run_name="__main__", alter_sys=True)'
            ),
        ],
        env={
            "a": 1,
            "b": 2,
            "c": 3,
            "PYTHONUNBUFFERED": "1",
            "PYTHONDEVMODE": "1",
            "PYTHONUTF8": "1",
        },
        cwd=dev_command.tools.home_path,
        bufsize=1,
        encoding="UTF-8",
        stream_output=False,
    )

    # There's no log streaming
    dev_command._stream_app_logs.assert_not_called()


def test_dev_run_console_with_args(dev_command, first_app, tmp_path):
    "The console app can be run in dev mode with arguments"
    # Modify the app to be a console app
    first_app.console_app = True

    dev_command._stream_app_logs = mock.MagicMock()

    dev_command.run_dev_app(
        first_app,
        env={"a": 1, "b": 2, "c": 3},
        passthrough=["foo", "bar", "--whiz"],
    )

    dev_command.tools.subprocess.run.assert_called_once_with(
        [
            sys.executable,
            "-c",
            (
                "import runpy, sys;"
                "sys.path.pop(0);"
                "sys.argv.extend(['foo', 'bar', '--whiz']);"
                'runpy.run_module("first", run_name="__main__", alter_sys=True)'
            ),
        ],
        env={
            "a": 1,
            "b": 2,
            "c": 3,
            "PYTHONUNBUFFERED": "1",
            "PYTHONDEVMODE": "1",
            "PYTHONUTF8": "1",
        },
        cwd=dev_command.tools.home_path,
        bufsize=1,
        encoding="UTF-8",
        stream_output=False,
    )

    # No attempt to stream logs
    dev_command._stream_app_logs.assert_not_called()
