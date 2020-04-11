from unittest.mock import MagicMock

import pytest

from briefcase.integrations.android_sdk import AndroidSDK


@pytest.fixture
def mock_sdk(tmp_path):
    command = MagicMock()
    command.subprocess = MagicMock()

    sdk = AndroidSDK(command, root_path=tmp_path / 'sdk')

    return sdk
