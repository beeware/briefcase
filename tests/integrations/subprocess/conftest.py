from unittest.mock import MagicMock

import pytest

from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def mock_sub():
    command = MagicMock()
    command.verbosity = 0

    sub = Subprocess(command)
    sub._subprocess = MagicMock()

    return sub
