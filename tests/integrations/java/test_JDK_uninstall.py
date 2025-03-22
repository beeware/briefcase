from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import (
    BriefcaseCommandError,
)
from briefcase.integrations.base import ToolCache
from briefcase.integrations.java import JDK


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    mock_tools.host_os = "Windows"
    mock_tools.host_arch = "x86_64"
    return mock_tools


def test_java_running(mock_tools, tmp_path):
    """If Java is running, uninstall raised an error."""
    # Create a mock of a previously installed Java version.
    java_home = tmp_path / "tools/java"
    (java_home / "bin").mkdir(parents=True)

    # Create an JDK wrapper
    jdk = JDK(mock_tools, java_home=java_home)

    # Mock shutil.rmtree so that it gives a permission error
    mock_tools.shutil.rmtree.side_effect = PermissionError(
        "File is being used by other processes"
    )

    # Uninstalling JDK
    with pytest.raises(BriefcaseCommandError) as exc_info:
        jdk.uninstall()

    # Exception raised
    assert "Permission denied when trying to remove Java." in str(exc_info.value)
    assert "Ensure no Java processes are running and try again." in str(exc_info.value)


def test_java_not_running(mock_tools, tmp_path):
    """If Java is not running, uninstalling should proceed smoothly."""
    # Create a mock of a previously installed Java version.
    java_home = tmp_path / "tools/java"
    (java_home / "bin").mkdir(parents=True)

    # Create an JDK wrapper
    jdk = JDK(mock_tools, java_home=java_home)

    # Mock so that shutil behave normally
    mock_tools.shutil.rmtree = MagicMock()

    # Uninstall JDK
    jdk.uninstall()

    # Verify that shutil works normally
    assert mock_tools.shutil.rmtree.call_count == 1
