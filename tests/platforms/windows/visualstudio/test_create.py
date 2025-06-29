import pytest

from briefcase.console import Console
from briefcase.platforms.windows.visualstudio import WindowsVisualStudioCreateCommand

# Most tests are the same for both "app" and "visualstudio".
from ..app.test_create import *  # noqa: F403


@pytest.fixture
def create_command(tmp_path):
    return WindowsVisualStudioCreateCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_package_path(create_command, first_app_config, tmp_path):
    """The default package_path is passed as an absolute path."""
    context = create_command.output_format_template_context(first_app_config)
    assert context["package_path"] == str(
        tmp_path / "base_path/build/first-app/windows/visualstudio/x64/Release"
    )
