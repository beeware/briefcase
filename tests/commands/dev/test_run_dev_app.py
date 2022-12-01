import sys
from subprocess import CalledProcessError

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_subprocess_running_successfully(dev_command, first_app, tmp_path):
    dev_command.run_dev_app(
        first_app,
        env={"a": 1, "b": 2, "c": 3},
        test_mode=False,
    )
    dev_command.tools.subprocess.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-X",
            "dev",
            "-X",
            "utf8",
            "-c",
            (
                "import runpy, sys;"
                "sys.path.pop(0);"
                'runpy.run_module("first", run_name="__main__", alter_sys=True)'
            ),
        ],
        env={"a": 1, "b": 2, "c": 3},
        cwd=dev_command.tools.home_path,
        check=True,
    )


def test_subprocess_throws_error(dev_command, first_app, tmp_path):
    dev_command.tools.subprocess.run.side_effect = CalledProcessError(
        returncode=2, cmd="cmd"
    )
    with pytest.raises(
        BriefcaseCommandError,
        match="Problem running application 'first'",
    ):
        dev_command.run_dev_app(
            first_app,
            env={"a": 1, "b": 2, "c": 3},
            test_mode=False,
        )

    dev_command.tools.subprocess.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-X",
            "dev",
            "-X",
            "utf8",
            "-c",
            (
                "import runpy, sys;"
                "sys.path.pop(0);"
                'runpy.run_module("first", run_name="__main__", alter_sys=True)'
            ),
        ],
        env={"a": 1, "b": 2, "c": 3},
        cwd=dev_command.tools.home_path,
        check=True,
    )


def test_subprocess_test_mode_success(dev_command, first_app, tmp_path):
    "The test suite can be run in development mode"
    dev_command.run_dev_app(
        first_app,
        env={"a": 1, "b": 2, "c": 3},
        test_mode=True,
    )
    dev_command.tools.subprocess.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-X",
            "dev",
            "-X",
            "utf8",
            "-c",
            (
                "import runpy, sys;"
                "sys.path.pop(0);"
                'runpy.run_module("tests.first", run_name="__main__", alter_sys=True)'
            ),
        ],
        env={"a": 1, "b": 2, "c": 3},
        cwd=dev_command.tools.home_path,
        check=True,
    )


def test_subprocess_test_mode_failure(dev_command, first_app, tmp_path):
    "Failure in test mode raises a BriefcaseCommandError"
    dev_command.tools.subprocess.run.side_effect = CalledProcessError(
        returncode=2, cmd="cmd"
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Problem running test suite 'tests.first'",
    ):
        dev_command.run_dev_app(
            first_app,
            env={"a": 1, "b": 2, "c": 3},
            test_mode=True,
        )

    dev_command.tools.subprocess.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-X",
            "dev",
            "-X",
            "utf8",
            "-c",
            (
                "import runpy, sys;"
                "sys.path.pop(0);"
                'runpy.run_module("tests.first", run_name="__main__", alter_sys=True)'
            ),
        ],
        env={"a": 1, "b": 2, "c": 3},
        cwd=dev_command.tools.home_path,
        check=True,
    )
