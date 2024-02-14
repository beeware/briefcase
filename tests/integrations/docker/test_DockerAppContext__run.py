import subprocess
from unittest.mock import ANY

import pytest

from briefcase.console import LogLevel

# These tests ignore the elsewhere-tested complexities of Dockerizing
# the arguments and just focuses on the semantics of a run() call.


@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_simple_call(mock_tools, my_app, tmp_path, sub_stream_kw, capsys):
    """A simple call will be invoked."""

    mock_tools[my_app].app_context.run(["hello", "world"])

    mock_tools[my_app].app_context._dockerize_args.assert_called_once_with(
        ["hello", "world"]
    )
    # calls to run() default to using Popen() due to output streaming
    mock_tools.subprocess._subprocess.Popen.assert_called_once_with(
        ANY,
        env={"DOCKER_CLI_HINTS": "false", "PROCESS_ENV_VAR": "VALUE"},
        **sub_stream_kw,
    )
    assert capsys.readouterr().out == (
        "\n"
        "Entering Docker context...\n"
        "Docker| ------------------------------------------------------------------\n"
        "Docker| ------------------------------------------------------------------\n"
        "Leaving Docker context.\n"
        "\n"
    )


@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_interactive(mock_tools, my_app, tmp_path, sub_kw, capsys):
    """Docker can be invoked in interactive mode."""
    mock_tools[my_app].app_context.run(["hello", "world"], interactive=True)

    # Interactive Docker runs must disable output streaming
    mock_tools[my_app].app_context._dockerize_args.assert_called_once_with(
        ["hello", "world"],
        interactive=True,
        stream_output=False,
    )
    # Interactive means the call to run is direct, rather than going through Popen
    mock_tools.subprocess._subprocess.run.assert_called_once_with(
        ANY,
        env={"DOCKER_CLI_HINTS": "false", "PROCESS_ENV_VAR": "VALUE"},
        **sub_kw,
    )
    assert capsys.readouterr().out == (
        "\n"
        "Entering Docker context...\n"
        "Docker| ------------------------------------------------------------------\n"
        "Docker| ------------------------------------------------------------------\n"
        "Leaving Docker context.\n"
        "\n"
    )


@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_call_with_extra_kwargs(
    mock_tools,
    my_app,
    tmp_path,
    sub_stream_kw,
    capsys,
):
    """Extra keyword arguments are passed through as-is; env modifications are
    converted."""

    mock_tools[my_app].app_context.run(
        ["hello", "world"],
        encoding="ISO-42",
        extra_kw="extra",
    )

    mock_tools[my_app].app_context._dockerize_args.assert_called_once_with(
        ["hello", "world"],
        encoding="ISO-42",
        extra_kw="extra",
    )
    mock_tools.subprocess._subprocess.Popen.assert_called_once_with(
        ANY,
        extra_kw="extra",
        encoding="ISO-42",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True,
        errors="backslashreplace",
        env={"DOCKER_CLI_HINTS": "false", "PROCESS_ENV_VAR": "VALUE"},
    )
    assert capsys.readouterr().out == (
        "\n"
        "Entering Docker context...\n"
        "Docker| ------------------------------------------------------------------\n"
        "Docker| ------------------------------------------------------------------\n"
        "Leaving Docker context.\n"
        "\n"
    )


@pytest.mark.usefixtures("mock_docker")
@pytest.mark.usefixtures("mock_docker_app_context")
def test_simple_verbose_call(mock_tools, my_app, tmp_path, sub_stream_kw, capsys):
    """If verbosity is turned out, there is output."""
    mock_tools[my_app].app_context.tools.logger.verbosity = LogLevel.DEBUG

    mock_tools[my_app].app_context.run(["hello", "world"])

    mock_tools[my_app].app_context._dockerize_args.assert_called_once_with(
        ["hello", "world"],
    )
    mock_tools.subprocess._subprocess.Popen.assert_called_once_with(
        ANY,
        env={"DOCKER_CLI_HINTS": "false", "PROCESS_ENV_VAR": "VALUE"},
        **sub_stream_kw,
    )
    console_output = capsys.readouterr().out
    assert "Entering Docker context...\n" in console_output
    assert "Docker| >>> Running Command:\n" in console_output
