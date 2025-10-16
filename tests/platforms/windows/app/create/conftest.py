import pytest

from briefcase.platforms.windows.app import WindowsAppCreateCommand


@pytest.fixture
def create_command(dummy_console, tmp_path):
    return WindowsAppCreateCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
