import shutil
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_command(tmp_path):
    command = MagicMock()
    command.host_arch = "wonky"
    command.tools_path = tmp_path / "tools"
    command.tools_path.mkdir()

    command.shutil = shutil

    # Create a dummy bundle path
    (tmp_path / "bundle").mkdir()

    return command
