import pytest

from briefcase.exceptions import UnsupportedHostError
from briefcase.platforms.web.static import StaticWebCreateCommand


@pytest.fixture
def create_command(dummy_console, tmp_path):
    return StaticWebCreateCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


@pytest.mark.parametrize("host_os", ["WeirdOS"])
def test_unsupported_host_os(create_command, host_os):
    """Error raised for an unsupported OS."""
    create_command.tools.host_os = host_os

    with pytest.raises(UnsupportedHostError, match="This command is not supported on"):
        create_command()
