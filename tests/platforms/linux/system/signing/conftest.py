from unittest import mock

import pytest

from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.system import LinuxSystemPackageCommand

JANE = "5F0B07E0E2D05DD5611BF7A3F9FCBC4A7701B685"
BOB = "B6C8B38C96FFE1E6A1C66C9F4D68E1A93D2F47FB"


@pytest.fixture
def package_command(mock_tools, dummy_console, first_app, tmp_path):
    command = LinuxSystemPackageCommand(
        console=dummy_console,
        tools=mock_tools,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    mock_tools.host_os = "Linux"

    # Run outside docker for these tests.
    command.target_image = None

    # Mock the detection of system python.
    command.verify_system_python = mock.MagicMock()
    command.verify_system_packages = mock.MagicMock()

    # Mock the packaging tools.
    command._verify_packaging_tools = mock.MagicMock()

    # Provide an app context for the app.
    command.tools[first_app].app_context = mock.MagicMock(spec_set=Subprocess)

    return command
