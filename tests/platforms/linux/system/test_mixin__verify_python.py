import sys
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import DockerAppContext


def test_match(create_command, first_app_config, capsys):
    """If the system python matches the target python, everything is OK."""
    first_app_config.python_version_tag = "3"
    first_app_config.target_image = "somevendor:surprising"

    create_command.tools[first_app_config].app_context = DockerAppContext(
        tools=create_command.tools,
        app=first_app_config,
    )

    # Mock a return value from Docker that matches the system Python
    create_command.tools[first_app_config].app_context.check_output = MagicMock(
        return_value=f"3.{sys.version_info.minor}\n"
    )

    # Verify python for the app
    create_command.verify_python(first_app_config)

    # The docker container was interrogated for a Python version
    create_command.tools[
        first_app_config
    ].app_context.check_output.assert_called_once_with(
        [
            "python3",
            "-c",
            (
                "import sys; "
                "print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            ),
        ]
    )

    # Warning message was not recorded
    assert "WARNING: Python version mismatch!" not in capsys.readouterr().out

    # The python version has been updated
    assert first_app_config.python_version_tag == f"3.{sys.version_info.minor}"


def test_mismatch(create_command, first_app_config, capsys):
    """If the system python doesn't match the target python, a warning is raised."""
    first_app_config.python_version_tag = "3"
    first_app_config.target_image = "somevendor:surprising"

    create_command.tools[first_app_config].app_context = DockerAppContext(
        tools=create_command.tools,
        app=first_app_config,
    )

    # Mock a return value from Docker that matches the system Python
    create_command.tools[first_app_config].app_context.check_output = MagicMock(
        return_value="3.42\n"
    )

    # Verify python for the app
    create_command.verify_python(first_app_config)

    # The docker container was interrogated for a Python version
    create_command.tools[
        first_app_config
    ].app_context.check_output.assert_called_once_with(
        [
            "python3",
            "-c",
            (
                "import sys; "
                "print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            ),
        ]
    )

    # Warning message was recorded
    assert "WARNING: Python version mismatch!" in capsys.readouterr().out

    # The python version has been updated
    assert first_app_config.python_version_tag == "3.42"


def test_target_too_old(create_command, first_app_config):
    """If the target python is too old, an error is raised."""
    first_app_config.python_version_tag = "3"
    first_app_config.target_image = "somevendor:surprising"

    create_command.logger.warning = MagicMock()
    create_command.tools[first_app_config].app_context = DockerAppContext(
        tools=create_command.tools,
        app=first_app_config,
    )

    # Mock a return value from Docker that is too old for Briefcase
    create_command.tools[first_app_config].app_context.check_output = MagicMock(
        return_value="3.7.16\n"
    )

    # Verify python for the app
    with pytest.raises(
        BriefcaseCommandError,
        match=r"The system python3 version provided by somevendor:surprising "
        r"is 3\.7\.16; Briefcase requires a minimum Python3 version of 3\.8\.",
    ):
        create_command.verify_python(first_app_config)

    # The docker container was interrogated for a Python version
    create_command.tools[
        first_app_config
    ].app_context.check_output.assert_called_once_with(
        [
            "python3",
            "-c",
            (
                "import sys; "
                "print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            ),
        ]
    )
