import subprocess
from unittest.mock import ANY

import pytest

from briefcase.console import LogLevel

# These tests ignore the elsewhere-tested complexities of Dockerizing
# the arguments and just focuses on the semantics of a check_output() call.


@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_simple_call(mock_tools, my_app, tmp_path, sub_check_output_kw, capsys):
    """A simple call will be invoked."""
    output = mock_tools[my_app].app_context.check_output(["hello", "world"])

    assert output == "goodbye\n"
    mock_tools[my_app].app_context._dockerize_args.assert_called_once_with(
        ["hello", "world"]
    )
    mock_tools.subprocess._subprocess.check_output.assert_called_with(
        ANY,
        env={"DOCKER_CLI_HINTS": "false", "PROCESS_ENV_VAR": "VALUE"},
        **sub_check_output_kw,
    )
    assert capsys.readouterr().out == ""


@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_call_with_extra_kwargs(mock_tools, my_app, tmp_path, capsys):
    """Extra keyword arguments are passed through to subprocess."""
    output = mock_tools[my_app].app_context.check_output(
        ["hello", "world"],
        encoding="ISO-42",
        extra="extra",
    )

    assert output == "goodbye\n"
    mock_tools[my_app].app_context._dockerize_args.assert_called_once_with(
        ["hello", "world"],
        encoding="ISO-42",
        extra="extra",
    )
    mock_tools.subprocess._subprocess.check_output.assert_called_once_with(
        ANY,
        extra="extra",
        encoding="ISO-42",
        stderr=subprocess.STDOUT,
        text=True,
        errors="backslashreplace",
        env={"DOCKER_CLI_HINTS": "false", "PROCESS_ENV_VAR": "VALUE"},
    )
    assert capsys.readouterr().out == ""


@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_simple_verbose_call(
    mock_tools,
    my_app,
    tmp_path,
    sub_check_output_kw,
    capsys,
):
    """If verbosity is turned out, there is output."""
    mock_tools[my_app].app_context.tools.logger.verbosity = LogLevel.DEBUG

    output = mock_tools[my_app].app_context.check_output(["hello", "world"])

    assert output == "goodbye\n"
    mock_tools[my_app].app_context._dockerize_args.assert_called_once_with(
        ["hello", "world"]
    )
    mock_tools.subprocess._subprocess.check_output.assert_called_once_with(
        ANY,
        env={"DOCKER_CLI_HINTS": "false", "PROCESS_ENV_VAR": "VALUE"},
        **sub_check_output_kw,
    )
    assert ">>> Running Command:\n" in capsys.readouterr().out
