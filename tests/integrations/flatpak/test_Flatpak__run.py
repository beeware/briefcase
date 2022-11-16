import subprocess
from unittest import mock


def test_run(flatpak):
    """A Flatpak project can be executed."""
    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    flatpak.tools.subprocess.Popen.return_value = log_popen

    # Call run()
    result = flatpak.run(
        bundle="com.example",
        app_name="my-app",
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
        bundle="com.example",
        app_name="my-app",
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
