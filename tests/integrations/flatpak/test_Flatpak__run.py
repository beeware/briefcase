import subprocess
from unittest import mock

import pytest

from briefcase.console import LogLevel


@pytest.mark.parametrize("tool_debug_mode", (True, False))
def test_run(flatpak, tool_debug_mode):
    """A Flatpak project can be executed."""
    # Enable verbose tool logging
    if tool_debug_mode:
        flatpak.tools.logger.verbosity = LogLevel.DEEP_DEBUG

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    flatpak.tools.subprocess.Popen.return_value = log_popen

    # Call run()
    result = flatpak.run(bundle_identifier="com.example.my-app")

    # The expected call was made
    flatpak.tools.subprocess.Popen.assert_called_once_with(
        [
            "flatpak",
            "run",
        ]
        + (["--verbose"] if tool_debug_mode else [])
        + ["com.example.my-app"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The popen object was returned.
    assert result == log_popen


@pytest.mark.parametrize("tool_debug_mode", (True, False))
def test_run_with_args(flatpak, tool_debug_mode):
    """A Flatpak project can be executed with additional arguments."""
    # Enable verbose tool logging
    if tool_debug_mode:
        flatpak.tools.logger.verbosity = LogLevel.DEEP_DEBUG

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    flatpak.tools.subprocess.Popen.return_value = log_popen

    # Call run()
    result = flatpak.run(
        bundle_identifier="com.example.my-app",
        args=["foo", "bar"],
    )

    # The expected call was made
    flatpak.tools.subprocess.Popen.assert_called_once_with(
        [
            "flatpak",
            "run",
        ]
        + (["--verbose"] if tool_debug_mode else [])
        + ["com.example.my-app"]
        + ["foo", "bar"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The popen object was returned.
    assert result == log_popen


def test_main_module_override(flatpak):
    """The main module can be overridden."""
    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    flatpak.tools.subprocess.Popen.return_value = log_popen

    # Call run()
    result = flatpak.run(
        bundle_identifier="com.example.my-app",
        main_module="org.beeware.test-case",
    )

    # The expected call was made
    flatpak.tools.subprocess.Popen.assert_called_once_with(
        [
            "flatpak",
            "run",
            "com.example.my-app",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={
            "BRIEFCASE_MAIN_MODULE": "org.beeware.test-case",
        },
    )

    # The popen object was returned.
    assert result == log_popen
