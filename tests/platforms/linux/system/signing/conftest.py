from unittest import mock

import pytest

from briefcase.integrations.gnupg import GnuPG
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.system import LinuxSystemPackageCommand

JANE = "5F0B07E0E2D05DD5611BF7A3F9FCBC4A7701B685"
BOB = "B6C8B38C96FFE1E6A1C66C9F4D68E1A93D2F47FB"


@pytest.fixture
def package_command(dummy_console, first_app, tmp_path):
    command = LinuxSystemPackageCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"

    # Run outside docker for these tests.
    command.target_image = None

    # Mock the detection of system python.
    command.verify_system_python = mock.MagicMock()
    command.verify_system_packages = mock.MagicMock()

    # Mock the packaging tools.
    command._verify_packaging_tools = mock.MagicMock()

    # Provide an app context for the app.
    command.tools[first_app].app_context = mock.MagicMock(spec_set=Subprocess)

    # Mock the GPG tool, so no identities are available by default.
    command.tools.gnupg = mock.MagicMock(spec_set=GnuPG)
    command.tools.gnupg.identities.return_value = {}

    return command
