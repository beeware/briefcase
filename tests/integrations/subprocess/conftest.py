import os
from unittest.mock import MagicMock

import pytest

from briefcase.integrations.subprocess import Subprocess
from briefcase.console import Log


@pytest.fixture
def mock_sub():
    command = MagicMock()
    command.logger = Log(verbosity=1)
    command.os = os

    sub = Subprocess(command)
    sub._subprocess = MagicMock()

    # mock the output of subprocess.run()
    run_result = MagicMock()
    run_result.returncode = 0
    sub._subprocess.run.return_value = run_result

    return sub
