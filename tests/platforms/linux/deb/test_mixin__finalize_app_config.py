import sys
from unittest.mock import MagicMock, call

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_docker(create_command, first_app_config):
    "An app can be finalized inside docker"
    # Build the app on a specific target
    create_command.target_image = "somevendor:surprising"
    create_command.tools.docker = MagicMock()
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Finalize the app config
    create_command.finalize_app_config(first_app_config)

    # The base image has been prepared
    create_command.tools.docker.prepare.assert_called_once_with("somevendor:surprising")

    # The app's image, vendor and codename have been constructed from the target image
    assert first_app_config.target_image == "somevendor:surprising"
    assert first_app_config.target_vendor == "somevendor"
    assert first_app_config.target_codename == "surprising"

    # Python source is implied to be system
    assert first_app_config.python_source == "system"

    # For tests of other properties merged in finalization, see
    # test_properties


def test_nodocker(create_command, first_app_config):
    "An app can be finalized without docker"
    # Build the app without docker
    create_command.target_image = None
    create_command.tools.subprocess.check_output = MagicMock(
        side_effect=[
            "SomeVendor\n",
            "Surprising\n",
        ]
    )
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Finalize the app config
    create_command.finalize_app_config(first_app_config)

    # lsb_release has been interrogated
    create_command.tools.subprocess.check_output.mock_calls = [
        call(["lsb_release", "-i", "-s"]),
        call(["lsb_release", "-c", "-s"]),
    ]

    # The app's image, vendor and codename have been constructed from the target image
    assert first_app_config.target_image == "somevendor:surprising"
    assert first_app_config.target_vendor == "somevendor"
    assert first_app_config.target_codename == "surprising"

    # Python source is implied to be system
    assert first_app_config.python_source == "system"

    # For tests of other properties merged in finalization, see
    # test_properties


def test_properties(create_command, first_app_config):
    """The final app config is the result of merging target properties, plus other derived properties."""
    # Run this test as "docker"; however, the things we're testing aren't docker specific.
    create_command.target_image = "somevendor:surprising"
    create_command.tools.docker = MagicMock()
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Augment the app config with some extra attributes
    first_app_config.python_source = "system"
    first_app_config.surprise_1 = "XXXX"
    first_app_config.surprise_9 = "9999"
    first_app_config.somevendor = {
        "surprising": {
            "surprise_1": "1111",
            "surprise_2": "2222",
        },
        "normal": {
            "surprise_1": "3333",
            "surprise_2": "4444",
        },
    }
    first_app_config.ubuntu = {
        "jammy": {
            "surprise_1": "5555",
        },
    }

    create_command.finalize_app_config(first_app_config)

    # The target's config attributes have been merged into the app
    assert first_app_config.surprise_1 == "1111"
    assert first_app_config.surprise_2 == "2222"
    assert first_app_config.surprise_9 == "9999"

    # The glibc version was determined
    assert first_app_config.glibc_version == "2.42"

    # Since it's system python, the python version is 3
    assert first_app_config.python_version_tag == "3"


def test_ubuntu_deadsnakes(create_command, first_app_config):
    # Build the app on a specific target
    create_command.target_image = "ubuntu:jammy"
    create_command.tools.docker = MagicMock()
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Configure the app to use deadsnakes on ubuntu
    first_app_config.ubuntu = {
        "jammy": {
            "python_source": "deadsnakes",
        },
    }

    # Finalize the app config
    create_command.finalize_app_config(first_app_config)

    # The app's image, vendor and codename have been constructed from the target image
    assert first_app_config.target_image == "ubuntu:jammy"
    assert first_app_config.target_vendor == "ubuntu"
    assert first_app_config.target_codename == "jammy"

    # Since it's deadsnakes python, the python version is the same as the host
    assert first_app_config.python_source == "deadsnakes"
    assert first_app_config.python_version_tag == f"3.{sys.version_info.minor}"


def test_non_ubuntu_deadsnakes(create_command, first_app_config):
    """Deadsnakes can only be specified on Ubuntu"""
    # Run this test as "docker"; however, the things we're testing aren't docker specific.
    create_command.target_image = "somevendor:surprising"
    create_command.tools.docker = MagicMock()
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Configure the app to use deadsnakes on ubuntu
    first_app_config.python_source = "deadsnakes"

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Deadsnakes can only be used to build Ubuntu packages\.",
    ):
        create_command.finalize_app_config(first_app_config)


def test_unknown_source(create_command, first_app_config):
    """Unknown python sources are ignored"""
    # Run this test as "docker"; however, the things we're testing aren't docker specific.
    create_command.target_image = "somevendor:surprising"
    create_command.tools.docker = MagicMock()
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Configure the app to use deadsnakes on ubuntu
    first_app_config.python_source = "mystery"

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unknown python source 'mystery'; should be one of 'system', 'deadsnakes'.",
    ):
        create_command.finalize_app_config(first_app_config)
