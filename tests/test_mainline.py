import sys
from pathlib import Path

import pytest

from briefcase.__main__ import main
from briefcase.commands.create import CreateCommand
from briefcase.commands.run import RunCommand
from briefcase.console import Console
from briefcase.exceptions import BriefcaseTestSuiteFailure, BriefcaseWarning

from .utils import create_file


@pytest.fixture
def pyproject_toml(monkeypatch, tmp_path):
    # Monkeypatch cwd() to use a test folder.
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    create_file(
        tmp_path / "pyproject.toml",
        """
[build-system]
requires = ["briefcase"]

[tool.briefcase]
project_name = "Hello World"
bundle = "com.example"
version = "0.0.1"
license.file = "LICENSE"

[tool.briefcase.app.myapp]
description = "My first application"
sources = ["myapp"]

    """,
    )


def test_help(monkeypatch, tmp_path, capsys):
    """Briefcase can output help."""
    # Set the test command line
    monkeypatch.setattr(sys, "argv", ["briefcase", "--help"])

    # Help has a return code of -10
    assert main() == -10

    output = capsys.readouterr().out
    assert output.startswith(
        "\nusage: briefcase [-h] <command> [<platform>] [<format>] ...\n"
    )

    # No log file was written
    assert len(list(tmp_path.glob(f"{Console.LOG_DIR}/briefcase.*.log"))) == 0


def test_command(monkeypatch, tmp_path, capsys):
    """A command can be successful."""
    # Monkeypatch cwd() to use a test folder.
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    # Create a dummy empty template to use in the new command
    create_file(tmp_path / "template/cookiecutter.json", '{"app_name": "app_name"}')
    create_file(tmp_path / "template/{{ cookiecutter.app_name }}/app", "content")

    # Set the test command line
    monkeypatch.setattr(
        sys,
        "argv",
        ["briefcase", "new", "--no-input", "--template", str(tmp_path / "template")],
    )

    # Successful return is 0
    assert main() == 0

    output = capsys.readouterr().out
    assert output.startswith(
        "\n[helloworld] Generating a new application 'Hello World'"
    )

    # No log file was written
    assert len(list(tmp_path.glob(f"{Console.LOG_DIR}/briefcase.*.log"))) == 0


def test_command_warning(monkeypatch, pyproject_toml, tmp_path, capsys):
    """A command can raise a known warning."""
    # Monkeypatch cwd() to use a test folder.
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    # Set the test command line
    monkeypatch.setattr(sys, "argv", ["briefcase", "create"])

    # Monkeypatch a warning into the create command
    def sort_of_bad_generate_app_template(self, app):
        raise BriefcaseWarning(error_code=0, msg="This is bad, but not *really* bad")

    monkeypatch.setattr(
        CreateCommand, "generate_app_template", sort_of_bad_generate_app_template
    )

    # The error code has been returned
    assert main() == 0

    # The warning has been output
    output = capsys.readouterr().out
    assert output.endswith("\nThis is bad, but not *really* bad\n")

    # Log files are not created for BriefcaseWarnings
    assert len(list(tmp_path.glob(f"{Console.LOG_DIR}/briefcase.*.create.log"))) == 0


def test_command_error(monkeypatch, tmp_path, capsys):
    """A command can raise a known error."""
    # Monkeypatch cwd() to use a test folder.
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    # Set the test command line
    monkeypatch.setattr(sys, "argv", ["briefcase", "create"])

    # BriefcaseConfigError has a return code of 100
    assert main() == 100

    output = capsys.readouterr().out
    assert output.startswith(
        "\nBriefcase configuration error: Configuration file not found."
    )

    # Log files are not created for BriefcaseConfigError errors
    assert len(list(tmp_path.glob(f"{Console.LOG_DIR}/briefcase.*.create.log"))) == 0


def test_unknown_command_error(monkeypatch, pyproject_toml, capsys):
    """A command can raise an unknown error."""
    monkeypatch.setattr(sys, "argv", ["briefcase", "create"])

    # Monkeypatch an error into the create command
    def bad_generate_app_template(self, app):
        raise ValueError("Bad value")

    monkeypatch.setattr(
        CreateCommand, "generate_app_template", bad_generate_app_template
    )

    # Error is surfaced to the user
    with pytest.raises(ValueError, match=r"Bad value"):
        main()


def test_interrupted_command(monkeypatch, pyproject_toml, tmp_path, capsys):
    """A command can be interrupted."""
    monkeypatch.setattr(sys, "argv", ["briefcase", "create"])

    # Monkeypatch a keyboard interrupt into the create command
    def interrupted_generate_app_template(self, app):
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        CreateCommand, "generate_app_template", interrupted_generate_app_template
    )

    # Interrupted command return -42
    assert main() == -42

    output = capsys.readouterr().out
    assert "\nAborted by user.\n" in output

    # No log file was written
    assert len(list(tmp_path.glob(f"{Console.LOG_DIR}/briefcase.*.create.log"))) == 0


def test_interrupted_command_with_log(monkeypatch, pyproject_toml, tmp_path, capsys):
    """A log can be generated when a command is interrupted."""
    monkeypatch.setattr(sys, "argv", ["briefcase", "create", "--log"])

    # Monkeypatch a keyboard interrupt into the create command
    def interrupted_generate_app_template(self, app):
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        CreateCommand, "generate_app_template", interrupted_generate_app_template
    )

    # Interrupted command return -42
    assert main() == -42

    output = capsys.readouterr().out
    assert "\nAborted by user.\n" in output

    # A log file was written
    assert len(list(tmp_path.glob(f"{Console.LOG_DIR}/briefcase.*.create.log"))) == 1


def test_test_failure(monkeypatch, pyproject_toml, tmp_path, capsys):
    """A test suite failure can be reported."""
    monkeypatch.setattr(sys, "argv", ["briefcase", "run", "--test"])

    # Monkeypatch a keyboard interrupt into the run command
    def run_call(self, **kwargs):
        raise BriefcaseTestSuiteFailure()

    monkeypatch.setattr(RunCommand, "__call__", run_call)

    # Failed test suite returns 1000
    assert main() == 1000

    # The code generating the test failure is responsible for output
    output = capsys.readouterr().out
    assert output == ""

    # Log files are not created for BriefcaseTestSuiteFailures
    assert len(list(tmp_path.glob(f"{Console.LOG_DIR}/briefcase.*.create.log"))) == 0
