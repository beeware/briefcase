import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import (
    BriefcaseCommandError,
)
from briefcase.integrations.java import JDK


@pytest.mark.parametrize(
    "host_os, java_home",
    [
        ("Linux", Path("tools", "java17")),
        ("Windows", Path("tools", "java17")),
        ("Darwin", Path("tools", "java17", "Contents", "Home")),
    ],
)
def test_java_running(mock_tools, host_os, java_home, tmp_path):
    """If Java is running, uninstall will raise an error message."""
    # Mock os
    mock_tools.host_os = host_os

    # Create a mock of a previously installed Java version.
    (tmp_path / java_home / "bin").mkdir(parents=True)

    # Create an JDK wrapper
    jdk = JDK(mock_tools, java_home=tmp_path / java_home)

    # Mock shutil.rmtree so that it gives a permission error
    mock_tools.shutil.rmtree.side_effect = PermissionError(
        "File is being used by other processes"
    )

    # Set correct path according to each OS
    if host_os == "Darwin":
        expected_loc = (tmp_path / java_home).parent.parent
    else:
        expected_loc = tmp_path / java_home

    # Attempting to uninstall JDK which will fail due to Permission Error
    with pytest.raises(
        BriefcaseCommandError,
        match=re.escape(f"Permission denied when trying to remove {expected_loc!r}"),
    ):
        jdk.uninstall()


@pytest.mark.parametrize(
    "host_os, java_home",
    [
        ("Linux", Path("tools", "java17")),
        ("Windows", Path("tools", "java17")),
        ("Darwin", Path("tools", "java17", "Contents", "Home")),
    ],
)
def test_java_not_running(mock_tools, host_os, java_home, tmp_path):
    """If Java is not running, uninstalling should proceed smoothly."""
    # Mock os
    mock_tools.host_os = host_os

    # Create a mock of a previously installed Java version.
    (tmp_path / java_home / "bin").mkdir(parents=True)

    # Create an JDK wrapper
    jdk = JDK(mock_tools, java_home=tmp_path / java_home)

    # Set correct path according to each OS
    if host_os == "Darwin":
        expected_loc = (tmp_path / java_home).parent.parent
    else:
        expected_loc = tmp_path / java_home

    # Mock so that shutil behave normally
    mock_tools.shutil.rmtree = MagicMock()

    # Uninstall JDK
    jdk.uninstall()

    # Verify that shutil works normally and that correct location is passed
    mock_tools.shutil.rmtree.assert_called_once_with(expected_loc)
