import subprocess
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.parametrize(
    "ldd_output, version",
    [
        # ubuntu:focal
        (
            [
                "ldd (Ubuntu GLIBC 2.31-0ubuntu9.9) 2.31",
                "Copyright (C) 2020 Free Software Foundation, Inc.",
                "...",
            ],
            "2.31",
        ),
        # fedora:37
        (
            [
                "ldd (GNU libc) 2.36",
                "Copyright (C) 2020 Free Software Foundation, Inc.",
                "...",
            ],
            "2.36",
        ),
        # arch:rolling (20230301)
        (
            [
                "ldd (GNU libc) 2.37",
                "Copyright (C) 2023 Free Software Foundation, Inc.",
                "...",
            ],
            "2.37",
        ),
    ],
)
def test_target_glibc_version_docker(
    create_command, first_app_config, ldd_output, version
):
    "Test that the glibc version in a docker container can be determined"
    # Mock an app being built on docker
    create_command.target_image = "somevendor:surprising"
    first_app_config.target_image = "somevendor:surprising"

    # Mock a verified Docker, and the output of ldd.
    create_command.tools.docker = MagicMock()
    create_command.tools.docker.check_output.return_value = "\n".join(ldd_output)

    # The glibc version was returned
    assert create_command.target_glibc_version(first_app_config) == version

    # Docker was consulted for the glibc version
    create_command.tools.docker.check_output.assert_called_once_with(
        ["ldd", "--version"],
        image_tag="somevendor:surprising",
    )


def test_target_glibc_version_docker_no_ldd(create_command, first_app_config):
    "If the Docker container can't run ldd, an error is raised"
    # Mock an app being built on docker
    create_command.target_image = "somevendor:surprising"
    first_app_config.target_image = "somevendor:surprising"

    # Mock a verified Docker, and an error from invoking ldd.
    create_command.tools.docker = MagicMock()
    create_command.tools.docker.check_output.side_effect = (
        subprocess.CalledProcessError(cmd=["docker ..."], returncode=-1)
    )

    # An error is raised when getting the glibc version
    with pytest.raises(
        BriefcaseCommandError, match=r"Unable to determine glibc dependency version."
    ):
        create_command.target_glibc_version(first_app_config)

    # Docker was consulted for the glibc version
    create_command.tools.docker.check_output.assert_called_once_with(
        ["ldd", "--version"],
        image_tag="somevendor:surprising",
    )


def test_target_glibc_version_docker_bad_ldd_output(create_command, first_app_config):
    "If ldd returns unexpected content, an error is raised"
    # Mock an app being built on docker
    create_command.target_image = "somevendor:surprising"
    first_app_config.target_image = "somevendor:surprising"

    # Mock a verified Docker, and unexpected ldd output
    create_command.tools.docker = MagicMock()
    create_command.tools.docker.check_output.return_value = (
        "I don't know what this is, but it isn't ldd output."
    )

    # An error is raised when getting the glibc version
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to parse glibc dependency version from version string.",
    ):
        create_command.target_glibc_version(first_app_config)

    # Docker was consulted for the glibc version
    create_command.tools.docker.check_output.assert_called_once_with(
        ["ldd", "--version"],
        image_tag="somevendor:surprising",
    )


def test_target_glibc_version_nodocker(create_command, first_app_config):
    "Test that the glibc version of the local system can be returned"
    # Mock a non-docker setup
    create_command.target_image = None
    create_command.tools.os.confstr = MagicMock(return_value="glibc 2.42")

    # The glibc version was returned
    assert create_command.target_glibc_version(first_app_config) == "2.42"

    # The OS module was consulted for the glibc version
    create_command.tools.os.confstr.assert_called_once_with("CS_GNU_LIBC_VERSION")
