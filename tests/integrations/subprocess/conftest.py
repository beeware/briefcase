import subprocess
import time
from unittest.mock import MagicMock

import pytest

from briefcase.integrations.subprocess import Subprocess

# hardcoded here since subprocess will only include these constants if Python is literally on Windows
CREATE_NO_WINDOW = 0x8000000
CREATE_NEW_PROCESS_GROUP = 0x200


@pytest.fixture
def mock_sub(mock_tools):
    mock_tools.os.environ = {
        "VAR1": "Value 1",
        "PS1": "\nLine 2\n\nLine 4",
        "PWD": "/home/user/",
    }

    sub = Subprocess(mock_tools)
    sub._subprocess = MagicMock(spec=subprocess)

    run_result = MagicMock(spec=subprocess.CompletedProcess)
    run_result.returncode = 0
    sub._subprocess.run.return_value = run_result

    sub._subprocess.check_output.return_value = "some output line 1\nmore output line 2"

    sub._subprocess.CREATE_NO_WINDOW = CREATE_NO_WINDOW
    sub._subprocess.CREATE_NEW_PROCESS_GROUP = CREATE_NEW_PROCESS_GROUP

    return sub


@pytest.fixture
def popen_process():
    process = MagicMock()

    # Mock the readline values of an actual process. The final return value is "",
    # indicating that the process has exited; however, we insert a short sleep
    # to ensure that any other threads will have a chance to run before this
    # thread actually terminates.
    def mock_readline():
        yield from [
            "output line 1\n",
            "\n",
            "output line 3\n",
        ]
        time.sleep(0.1)
        yield ""

    process.stdout.readline.side_effect = mock_readline()
    process.poll.return_value = -3
    return process
