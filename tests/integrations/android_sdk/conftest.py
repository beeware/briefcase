from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.integrations.android_sdk import AndroidSDK


@pytest.fixture
def mock_sdk(tmp_path):
    command = MagicMock()
    command.home_path = tmp_path
    command.subprocess = MagicMock()

    # Mock an empty environment
    command.os.environ = {}

    # Set a JAVA_HOME
    command.java_home_path = Path('/path/to/jdk')

    sdk = AndroidSDK(command, root_path=tmp_path / 'sdk')

    return sdk
