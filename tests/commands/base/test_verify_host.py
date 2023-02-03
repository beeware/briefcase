import pytest

from briefcase.exceptions import UnsupportedHostError


@pytest.mark.parametrize("host_os", ["Darwin", "Linux", "Windows"])
def test_default_os_support(base_command, host_os):
    base_command.tools.host_os = host_os
    base_command.verify_host()


def test_unsupported_os(base_command):
    base_command.tools.host_os = "WeirdOS"
    with pytest.raises(UnsupportedHostError, match="This command is not supported on"):
        base_command.verify_host()
