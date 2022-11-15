from briefcase.integrations.download import Download
from briefcase.integrations.subprocess import Subprocess


def test_base_tools_exist(base_command):
    """Ensure default tools are always available."""
    assert isinstance(base_command.tools.subprocess, Subprocess)
    assert isinstance(base_command.tools.download, Download)

    base_command.verify_tools()
