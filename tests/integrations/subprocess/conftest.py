from unittest.mock import MagicMock

import pytest

from briefcase.integrations.subprocess import Subprocess
from briefcase.commands.base import Log


@pytest.fixture
def mock_sub():
    command = MagicMock()
    command.logger = Log(verbosity=1)

    sub = Subprocess(command)
    sub._subprocess = MagicMock()

    return sub
