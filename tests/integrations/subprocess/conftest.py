from unittest.mock import MagicMock

import pytest

from briefcase.integrations.subprocess import Subprocess
from briefcase.console import Log

# hardcoded here since subprocess will only include these constants if Python is literally on Windows
CREATE_NO_WINDOW = 0x8000000
CREATE_NEW_PROCESS_GROUP = 0x200


@pytest.fixture
def mock_sub():
    command = MagicMock()
    command.logger = Log(verbosity=1)

    command.os = MagicMock()
    command.os.environ = {
        "VAR1": "Value 1",
        "PS1": "\nLine 2\n\nLine 4",
        "PWD": "/home/user/",
    }

    sub = Subprocess(command)
    sub._subprocess = MagicMock()

    run_result = MagicMock()
    run_result.returncode = 0
    sub._subprocess.run.return_value = run_result

    sub._subprocess.check_output.return_value = "some output line 1\nmore output line 2"

    sub._subprocess.CREATE_NO_WINDOW = CREATE_NO_WINDOW
    sub._subprocess.CREATE_NEW_PROCESS_GROUP = CREATE_NEW_PROCESS_GROUP

    return sub
