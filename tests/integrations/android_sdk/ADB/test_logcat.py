import subprocess
from unittest import mock

import pytest


@pytest.mark.parametrize("is_color_enabled", [True, False])
def test_logcat(mock_tools, adb, is_color_enabled, monkeypatch):
    """Invoking `logcat()` calls `Popen()` with the appropriate parameters."""
    # Mock whether color is enabled for the console
    monkeypatch.setattr(
        type(mock_tools.input),
        "is_color_enabled",
        mock.PropertyMock(return_value=is_color_enabled),
    )

    # Mock the result of calling Popen so we can compare against this return value
    popen = mock.MagicMock()
    mock_tools.subprocess.Popen.return_value = popen

    # Invoke logcat
    result = adb.logcat("1234")

    # Validate call parameters.
    mock_tools.subprocess.Popen.assert_called_once_with(
        [
            mock_tools.android_sdk.adb_path,
            "-s",
            "exampleDevice",
            "logcat",
            "--format=tag",
            "--pid",
            "1234",
            "EGL_emulation:S",
        ]
        + (["--format=color"] if is_color_enabled else []),
        env=mock_tools.android_sdk.env,
        encoding="UTF-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The Popen object is returned
    assert result == popen
