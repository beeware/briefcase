import os
import subprocess
from unittest import mock

import pytest

from briefcase.config import DraftAppConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.hooks.commands import CommandsHook
from briefcase.integrations.subprocess import Subprocess


class HookCommand:
    """The parts of a command that a hook uses."""

    platform = "iOS"
    output_format = "Xcode"
    command = "create"

    def __init__(self, tools, base_path):
        self.tools = tools
        self.console = tools.console
        self.base_path = base_path

    def bundle_path(self, app):
        return self.build_path(app) / "xcode"

    def build_path(self, app):
        return self.base_path / "build" / app.app_name / "ios"


def app_with(hooks):
    return DraftAppConfig(
        app_name="myapp",
        version="1.2.3",
        bundle="org.beeware",
        description="A simple app",
        sources=["src/myapp"],
        license={"file": "LICENSE"},
        hooks=hooks,
    )


def hook_env(command, app, stage):
    """The variables a hook command receives for a stage."""
    return {
        "BRIEFCASE_APP_NAME": "myapp",
        "BRIEFCASE_BUNDLE_PATH": str(command.bundle_path(app)),
        "BRIEFCASE_HOOK_STAGE": stage,
        "BRIEFCASE_OUTPUT_FORMAT": "Xcode",
        "BRIEFCASE_PLATFORM": "iOS",
    }


@pytest.fixture
def command(mock_tools, tmp_path):
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    return HookCommand(mock_tools, tmp_path / "project")


def test_name():
    """The hook is named after the setting it reads."""
    assert CommandsHook().name == "commands"


def test_no_commands_for_the_stage(command):
    """Stages without commands run nothing."""
    app = app_with({"post_create": [["echo", "created"]]})

    CommandsHook().invoke("pre_build", app, command)

    command.tools.subprocess.run.assert_not_called()


def test_commands_run_in_order(command):
    """Each command of the stage runs, in order, from the project directory."""
    app = app_with({"post_create": [["ruby", "patch.rb"], ["echo", "done"]]})

    CommandsHook().invoke("post_create", app, command)

    env = hook_env(command, app, "post_create")
    assert command.tools.subprocess.run.mock_calls == [
        mock.call(["ruby", "patch.rb"], check=True, cwd=command.base_path, env=env),
        mock.call(["echo", "done"], check=True, cwd=command.base_path, env=env),
    ]


def test_failing_command(command):
    """A command exiting non-zero stops the command with the exit code."""
    app = app_with({"post_create": [["ruby", "patch.rb"], ["echo", "done"]]})
    command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=3, cmd=["ruby", "patch.rb"]
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"post_create hook command 'ruby patch\.rb' for 'myapp' failed "
            r"\(exit code 3\)"
        ),
    ):
        CommandsHook().invoke("post_create", app, command)

    command.tools.subprocess.run.assert_called_once()


def test_missing_program(command):
    """A command whose program can't be started stops the command, naming it."""
    app = app_with({"pre_build": [["no-such-program", "--flag"]]})
    command.tools.subprocess.run.side_effect = FileNotFoundError(
        2, "No such file or directory", "no-such-program"
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"pre_build hook command 'no-such-program --flag' for 'myapp' "
            r"could not be run: .*No such file or directory"
        ),
    ):
        CommandsHook().invoke("pre_build", app, command)


@pytest.fixture
def process():
    """A process that prints one line, then exits successfully."""
    # Popen sets stdout and stderr in __init__, so spec_set can't describe them.
    process = mock.MagicMock(spec=subprocess.Popen)
    process.stdout = mock.MagicMock()
    # stderr goes to stdout, so the process has no stderr of its own.
    process.stderr = None
    process.stdout.readline.side_effect = ["patched\n", ""]
    process.poll.return_value = 0
    return process


@pytest.fixture
def streaming_command(mock_tools, tmp_path, process):
    """A command whose tools run processes through Briefcase's Subprocess wrapper, over
    a mocked operating system."""
    mock_tools.os.environ = {"VAR1": "Value 1"}
    mock_tools.subprocess = Subprocess(mock_tools)
    mock_tools.subprocess._subprocess = mock.MagicMock(spec_set=subprocess)
    popen = mock_tools.subprocess._subprocess.Popen
    popen.return_value.__enter__.return_value = process
    return HookCommand(mock_tools, tmp_path / "project")


def test_subprocess_environment_and_output(
    streaming_command,
    capsys,
    sub_stream_kw,
    sleep_zero,
):
    """The process starts from the project directory, with the user's environment and
    the hook's variables, and its output is shown."""
    app = app_with({"post_create": [["ruby", "patch.rb"]]})

    CommandsHook().invoke("post_create", app, streaming_command)

    streaming_command.tools.subprocess._subprocess.Popen.assert_called_once_with(
        ["ruby", "patch.rb"],
        cwd=os.fsdecode(streaming_command.base_path),
        env={"VAR1": "Value 1", **hook_env(streaming_command, app, "post_create")},
        **sub_stream_kw,
    )
    assert "patched\n" in capsys.readouterr().out


def test_subprocess_exit_code(streaming_command, process, sleep_zero):
    """A process exiting non-zero reports its exit code."""
    app = app_with({"pre_build": [["ruby", "patch.rb"]]})
    process.poll.return_value = 3

    with pytest.raises(BriefcaseCommandError, match=r"failed \(exit code 3\)"):
        CommandsHook().invoke("pre_build", app, streaming_command)


def test_subprocess_missing_program(streaming_command, sleep_zero):
    """A program that can't be started is reported, not raised as an OS error."""
    app = app_with({"pre_build": [["briefcase-no-such-program"]]})
    streaming_command.tools.subprocess._subprocess.Popen.side_effect = (
        FileNotFoundError(2, "No such file or directory", "briefcase-no-such-program")
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"'briefcase-no-such-program' for 'myapp' could not be run",
    ):
        CommandsHook().invoke("pre_build", app, streaming_command)
