from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.windows.visualstudio import WindowsVisualStudioCreateCommand

# Most tests and fixtures are the same for both "app" and "visualstudio". This file only
# contains those that need to be overridden.
from ..app.create.test_create import *  # noqa: F403


@pytest.fixture
def create_command(dummy_console, tmp_path):
    return WindowsVisualStudioCreateCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_package_path(create_command, first_app_config, tmp_path):
    """The default package_path is passed as an absolute path."""
    context = create_command.output_format_template_context(first_app_config)
    assert context["package_path"] == str(
        tmp_path / "base_path/build/first-app/windows/visualstudio/x64/Release"
    )


@pytest.mark.parametrize(
    ("min_os_version", "compatible"), [("7601", False), ("10240", True)]
)
def test_in_os_version(create_command, first_app_templated, min_os_version, compatible):
    """If the app defines a min OS version that is incompatible with the support
    package, an error is raised."""
    first_app_templated.requires = ["first", "second==1.2.3", "third>=3.2.1"]
    first_app_templated.min_os_version = min_os_version
    create_command.tools[first_app_templated].app_context = MagicMock(
        spec_set=Subprocess
    )

    if not compatible:
        with pytest.raises(
            BriefcaseCommandError,
            match=(
                r"Your Windows app specifies a minimum build number of 7601, "
                r"but the support package only supports 10240"
            ),
        ):
            create_command.install_app_requirements(first_app_templated)
        create_command.tools[first_app_templated].app_context.run.assert_not_called()
    else:
        create_command.install_app_requirements(first_app_templated)
        create_command.tools[first_app_templated].app_context.run.assert_called()
