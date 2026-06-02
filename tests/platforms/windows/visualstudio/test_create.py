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
    ("template_version", "app_version", "compatible"),
    [
        (10240, "7601", False),
        (10240, "10240", True),
        (10240, "17763", True),
        (None, 10240, True),
        (10240, None, True),
        (None, None, True),
    ],
)
def test_min_os_version(
    create_command, first_app_templated, template_version, app_version, compatible
):
    """If the app defines a min OS version that is incompatible with the app template,
    an error is raised."""
    first_app_templated.requires = ["first", "second==1.2.3", "third>=3.2.1"]
    create_command.target_windows_build = MagicMock(return_value=template_version)
    if app_version:
        first_app_templated.min_os_version = app_version
    create_command.tools[first_app_templated].app_context = MagicMock(
        spec_set=Subprocess
    )
    if not compatible:
        with pytest.raises(
            BriefcaseCommandError,
            match=(
                f"Your Windows app specifies a minimum build number of {app_version}, "
                f"but the app template only supports {template_version}"
            ),
        ):
            create_command.install_app_requirements(first_app_templated)
        create_command.tools[first_app_templated].app_context.run.assert_not_called()
    else:
        create_command.install_app_requirements(first_app_templated)
        create_command.tools[first_app_templated].app_context.run.assert_called()


def test_target_windows_build(create_command, first_app_templated):
    "Test that the target Windows build is returned"

    create_command._briefcase_toml[first_app_templated] = {"briefcase": {}}
    assert create_command.target_windows_build(first_app_templated) is None
    create_command._briefcase_toml[first_app_templated] = {
        "briefcase": {"target_windows_build": 10240}
    }
    assert create_command.target_windows_build(first_app_templated) == 10240
