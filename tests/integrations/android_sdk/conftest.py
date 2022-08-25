import platform
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.console import Log
from briefcase.integrations.android_sdk import AndroidSDK
from tests.utils import DummyConsole


@pytest.fixture
def mock_sdk(tmp_path):
    command = MagicMock()
    command.home_path = tmp_path / "home"
    command.data_path = tmp_path / "data"
    command.subprocess = MagicMock()
    command.input = DummyConsole()
    command.logger = Log(verbosity=1)

    command.host_arch = platform.machine()
    command.host_os = platform.system()

    # Mock an empty environment
    command.os.environ = {}

    # Set up a JDK
    jdk = MagicMock()
    jdk.java_home = Path("/path/to/jdk")

    sdk_root = tmp_path / "sdk"
    sdk_root.mkdir(parents=True)

    sdk = AndroidSDK(command, jdk=jdk, root_path=sdk_root)

    return sdk
