from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.docker import Docker
from briefcase.integrations.subprocess import Subprocess


@pytest.fixture
def mock_docker(tmp_path):
    command = MagicMock()
    command.logger = Log()
    command.input = Console()
    command.base_path = tmp_path / "base"
    command.platform_path = tmp_path / "platform"
    command.bundle_path.return_value = tmp_path / "bundle"
    command.dot_briefcase_path = tmp_path / ".briefcase"
    command.docker_image_tag.return_value = "briefcase/com.example.myapp:py3.X"
    command.python_version_tag = "3.X"
    command.os.getuid.return_value = "37"
    command.os.getgid.return_value = "42"

    command.subprocess = Subprocess(command)
    command.subprocess._subprocess = MagicMock()

    proc = MagicMock()
    proc.returncode = 3
    command.subprocess._subprocess.run.return_value = proc

    # Short circuit the process streamer
    wait_bar_streamer = MagicMock()
    wait_bar_streamer.stdout.readline.return_value = ""
    wait_bar_streamer.poll.return_value = 0
    command.subprocess._subprocess.Popen.return_value.__enter__.return_value = (
        wait_bar_streamer
    )

    app = MagicMock()
    app.app_name = "myapp"
    app.sources = ["path/to/src/myapp", "other/stuff"]
    app.system_requires = ["things==1.2", "stuff>=3.4"]

    docker = Docker(command, app)

    return docker
