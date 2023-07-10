import sys
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.linux import parse_freedesktop_os_release
from briefcase.platforms.linux.system import LinuxSystemRunCommand

from ....utils import create_file


def test_docker(create_command, first_app_config):
    """An app can be finalized inside docker."""
    # Build the app on a specific target
    create_command.target_image = "somevendor:surprising"
    create_command.tools.docker = MagicMock()
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Mock a minimal response from checking /etc/os-release
    create_command.tools.docker.check_output.return_value = "\n".join(
        [
            "ID=somevendor",
            "VERSION_CODENAME=surprising",
            "ID_LIKE=debian",
        ]
    )

    # Finalize the app config
    create_command.finalize_app_config(first_app_config)

    # The app's image, vendor and codename have been constructed from the target image
    assert first_app_config.target_image == "somevendor:surprising"
    assert first_app_config.target_vendor == "somevendor"
    assert first_app_config.target_codename == "surprising"
    assert first_app_config.target_vendor_base == "debian"

    # For tests of other properties merged in finalization, see
    # test_properties


def test_nodocker(create_command, first_app_config, tmp_path):
    """An app can be finalized without docker."""
    # Build the app without docker
    create_command.target_image = None
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    os_release = "\n".join(
        [
            "ID=somevendor",
            "VERSION_CODENAME=surprising",
            "ID_LIKE=debian",
        ]
    )
    if sys.version_info >= (3, 10):
        # mock platform.freedesktop_os_release()
        create_command.tools.platform.freedesktop_os_release = MagicMock(
            return_value=parse_freedesktop_os_release(os_release)
        )
    else:
        # For Pre Python3.10, mock the /etc/release file
        create_file(tmp_path / "os-release", os_release)
        create_command.tools.ETC_OS_RELEASE = tmp_path / "os-release"

    # Finalize the app config
    create_command.finalize_app_config(first_app_config)

    # The app's image, vendor and codename have been constructed from the target image
    assert first_app_config.target_image == "somevendor:surprising"
    assert first_app_config.target_vendor == "somevendor"
    assert first_app_config.target_codename == "surprising"
    assert first_app_config.target_vendor_base == "debian"

    # For tests of other properties merged in finalization, see
    # test_properties


def test_nodocker_non_freedesktop(create_command, first_app_config, tmp_path):
    """If the system isn't FreeDesktop compliant raise an error."""
    # Build the app without docker
    create_command.target_image = None
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    if sys.version_info >= (3, 10):
        # mock platform.freedesktop_os_release()
        create_command.tools.platform.freedesktop_os_release = MagicMock(
            side_effect=FileNotFoundError
        )
    else:
        # For Pre Python3.10, mock the /etc/release file
        # but don't create the file
        create_command.tools.ETC_OS_RELEASE = tmp_path / "os-release"

    # Finalize the app config
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Could not find the /etc/os-release file. Is this a FreeDesktop-compliant Linux distribution\?",
    ):
        create_command.finalize_app_config(first_app_config)


def test_docker_arch_with_user_mapping(create_command, first_app_config, tmp_path):
    """If Docker is mapping users and the host system is Arch, an error is raised."""
    # Build the app on a specific target
    create_command.target_image = "somearch:surprising"
    create_command.tools.host_os = "Linux"
    create_command.tools.docker = MagicMock()
    create_command.tools.docker.is_user_mapped = True
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Mock a minimal response for an Arch /etc/os-release
    create_command.tools.docker.check_output.return_value = "\n".join(
        [
            "ID=arch",
            "VERSION_ID=20230625.0.160368",
        ]
    )

    # Finalize the app config
    with pytest.raises(
        BriefcaseCommandError,
        match="Briefcase cannot use this Docker installation",
    ):
        create_command.finalize_app_config(first_app_config)


def test_docker_arch_with_user_mapping_macOS(
    create_command, first_app_config, tmp_path
):
    """If we're on macOS, and the host system is Arch, we can finalize even though macOS
    does user mapping."""
    # Build the app on a specific target
    create_command.target_image = "somearch:surprising"
    create_command.tools.host_os = "Darwin"
    create_command.tools.docker = MagicMock()
    create_command.tools.docker.is_user_mapped = True
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Mock a minimal response for an Arch /etc/os-release
    create_command.tools.docker.check_output.return_value = "\n".join(
        [
            "ID=arch",
            "VERSION_ID=20230625.0.160368",
        ]
    )

    # Finalize the app config
    create_command.finalize_app_config(first_app_config)

    # The app's image, vendor and codename have been constructed from the target image
    assert first_app_config.target_image == "somearch:surprising"
    assert first_app_config.target_vendor == "arch"
    assert first_app_config.target_codename == "20230625"
    assert first_app_config.target_vendor_base == "arch"


def test_docker_arch_without_user_mapping(create_command, first_app_config, tmp_path):
    """If Docker is *not* mapping users and the host system is Arch, an error is not
    raised."""
    # Build the app on a specific target
    create_command.target_image = "somearch:surprising"
    create_command.tools.host_os = "Linux"
    create_command.tools.docker = MagicMock()
    create_command.tools.docker.is_user_mapped = False
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Mock a minimal response for an Arch /etc/os-release
    create_command.tools.docker.check_output.return_value = "\n".join(
        [
            "ID=arch",
            "VERSION_ID=20230625.0.160368",
        ]
    )

    # Finalize the app config
    create_command.finalize_app_config(first_app_config)

    # The app's image, vendor and codename have been constructed from the target image
    assert first_app_config.target_image == "somearch:surprising"
    assert first_app_config.target_vendor == "arch"
    assert first_app_config.target_codename == "20230625"
    assert first_app_config.target_vendor_base == "arch"


def test_properties(create_command, first_app_config):
    """The final app config is the result of merging target properties, plus other
    derived properties."""
    # Run this test as "docker"; however, the things we're testing aren't docker specific.
    create_command.target_image = "somevendor:surprising"
    create_command.tools.docker = MagicMock()
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Mock a minimal response from checking /etc/os-release
    create_command.tools.docker.check_output.return_value = "\n".join(
        [
            "ID=somevendor",
            "VERSION_CODENAME=surprising",
            "ID_LIKE=debian",
        ]
    )

    # Augment the app config with some extra attributes
    first_app_config.surprise_0 = "AAAA"
    first_app_config.surprise_1 = "BBBB"
    first_app_config.surprise_2 = "CCCC"
    first_app_config.surprise_3 = "DDDD"

    first_app_config.debian = {
        "surprise_1": "1111",
        "surprise_2": "1112",
        "surprise_3": "1113",
        "surprise_4": "1114",
    }
    first_app_config.somevendor = {
        "surprise_2": "2222",
        "surprise_3": "2223",
        "surprise_5": "2225",
        # A version config that will override
        "surprising": {
            "surprise_3": "3333",
            "surprise_6": "3336",
        },
        # A version config that will be ignored
        "normal": {
            "surprise_1": "XXXX",
        },
    }
    # A different vendor and version that will be ignored
    first_app_config.ubuntu = {
        "surprise_1": "YYYY",
        "jammy": {
            "surprise_1": "ZZZZ",
        },
    }

    create_command.finalize_app_config(first_app_config)

    # The target's config attributes have been merged into the app
    # Base app properties that aren't overwritten persist
    assert first_app_config.surprise_0 == "AAAA"
    # Properties can be overwritten at the base vendor level
    assert first_app_config.surprise_1 == "1111"
    # Properties can be overwritten at the vendor level
    assert first_app_config.surprise_2 == "2222"
    # Properties can be overwritten at the version level
    assert first_app_config.surprise_3 == "3333"

    # New properties can be defined at the base vendor level
    assert first_app_config.surprise_4 == "1114"
    # New properties can be defined at the vendor level
    assert first_app_config.surprise_5 == "2225"
    # New properties can be defined at the version level
    assert first_app_config.surprise_6 == "3336"

    # The glibc version was determined
    assert first_app_config.glibc_version == "2.42"

    # Since it's system python, the python version is 3
    assert first_app_config.python_version_tag == "3"


def test_properties_unknown_basevendor(create_command, first_app_config):
    """If the base vendor can't be identified, the merge still succeeds."""
    # Run this test as "docker"; however, the things we're testing aren't docker specific.
    create_command.target_image = "somevendor:surprising"
    create_command.tools.docker = MagicMock()
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Mock a minimal response from checking /etc/os-release
    create_command.tools.docker.check_output.return_value = "\n".join(
        [
            "ID=somevendor",
            "VERSION_CODENAME=surprising",
        ]
    )

    # Augment the app config with some extra attributes
    first_app_config.surprise_0 = "AAAA"
    first_app_config.surprise_1 = "BBBB"
    first_app_config.surprise_2 = "CCCC"
    first_app_config.surprise_3 = "DDDD"

    first_app_config.somevendor = {
        "surprise_2": "2222",
        "surprise_3": "2223",
        "surprise_5": "2225",
        # A version config that will override
        "surprising": {
            "surprise_3": "3333",
            "surprise_6": "3336",
        },
        # A version config that will be ignored
        "normal": {
            "surprise_1": "XXXX",
        },
    }
    # A different vendor and version that will be ignored
    first_app_config.ubuntu = {
        "surprise_1": "YYYY",
        "jammy": {
            "surprise_1": "ZZZZ",
        },
    }

    create_command.finalize_app_config(first_app_config)

    # The target's config attributes have been merged into the app
    # Base app properties that aren't overwritten persist
    assert first_app_config.surprise_0 == "AAAA"
    assert first_app_config.surprise_1 == "BBBB"
    # Properties can be overwritten at the vendor level
    assert first_app_config.surprise_2 == "2222"
    # Properties can be overwritten at the version level
    assert first_app_config.surprise_3 == "3333"

    # The glibc version was determined
    assert first_app_config.glibc_version == "2.42"

    # Since it's system python, the python version is 3
    assert first_app_config.python_version_tag == "3"


def test_properties_no_basevendor_config(create_command, first_app_config):
    """If there's no basevendor config, the merge still succeeds."""
    # Run this test as "docker"; however, the things we're testing aren't docker specific.
    create_command.target_image = "somevendor:surprising"
    create_command.tools.docker = MagicMock()
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Mock a minimal response from checking /etc/os-release
    create_command.tools.docker.check_output.return_value = "\n".join(
        [
            "ID=somevendor",
            "VERSION_CODENAME=surprising",
            "ID_LIKE=debian",
        ]
    )

    # Augment the app config with some extra attributes
    first_app_config.surprise_0 = "AAAA"
    first_app_config.surprise_1 = "BBBB"
    first_app_config.surprise_2 = "CCCC"
    first_app_config.surprise_3 = "DDDD"

    first_app_config.somevendor = {
        "surprise_2": "2222",
        "surprise_3": "2223",
        "surprise_5": "2225",
        # A version config that will override
        "surprising": {
            "surprise_3": "3333",
            "surprise_6": "3336",
        },
        # A version config that will be ignored
        "normal": {
            "surprise_1": "XXXX",
        },
    }
    # A different vendor and version that will be ignored
    first_app_config.ubuntu = {
        "surprise_1": "YYYY",
        "jammy": {
            "surprise_1": "ZZZZ",
        },
    }

    create_command.finalize_app_config(first_app_config)

    # The target's config attributes have been merged into the app
    # Base app properties that aren't overwritten persist
    assert first_app_config.surprise_0 == "AAAA"
    assert first_app_config.surprise_1 == "BBBB"
    # Properties can be overwritten at the vendor level
    assert first_app_config.surprise_2 == "2222"
    # Properties can be overwritten at the version level
    assert first_app_config.surprise_3 == "3333"

    # The glibc version was determined
    assert first_app_config.glibc_version == "2.42"

    # Since it's system python, the python version is 3
    assert first_app_config.python_version_tag == "3"


def test_properties_no_vendor(create_command, first_app_config):
    """If there's no vendor-specific config, the merge succeeds."""
    # Run this test as "docker"; however, the things we're testing aren't docker specific.
    create_command.target_image = "somevendor:surprising"
    create_command.tools.docker = MagicMock()
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Mock a minimal response from checking /etc/os-release
    create_command.tools.docker.check_output.return_value = "\n".join(
        [
            "ID=somevendor",
            "VERSION_CODENAME=surprising",
            "ID_LIKE=debian",
        ]
    )

    # Augment the app config with some extra attributes
    first_app_config.surprise_0 = "AAAA"
    first_app_config.surprise_1 = "BBBB"
    first_app_config.surprise_2 = "CCCC"
    first_app_config.surprise_3 = "DDDD"

    first_app_config.debian = {
        "surprise_1": "1111",
        "surprise_2": "1112",
        "surprise_3": "1113",
    }
    # A different vendor and version that will be ignored
    first_app_config.ubuntu = {
        "surprise_1": "YYYY",
        "jammy": {
            "surprise_1": "ZZZZ",
        },
    }

    create_command.finalize_app_config(first_app_config)

    # The target's config attributes have been merged into the app
    # Base app properties that aren't overwritten persist
    assert first_app_config.surprise_0 == "AAAA"
    # Properties can be overwritten at the base vendor level
    assert first_app_config.surprise_1 == "1111"
    assert first_app_config.surprise_2 == "1112"
    assert first_app_config.surprise_3 == "1113"

    # The glibc version was determined
    assert first_app_config.glibc_version == "2.42"

    # Since it's system python, the python version is 3
    assert first_app_config.python_version_tag == "3"


def test_properties_no_version(create_command, first_app_config):
    """If there's no version-specific config, the merge succeeds."""
    # Run this test as "docker"; however, the things we're testing aren't docker specific.
    create_command.target_image = "somevendor:surprising"
    create_command.tools.docker = MagicMock()
    create_command.target_glibc_version = MagicMock(return_value="2.42")

    # Mock a minimal response from checking /etc/os-release
    create_command.tools.docker.check_output.return_value = "\n".join(
        [
            "ID=somevendor",
            "VERSION_CODENAME=surprising",
            "ID_LIKE=debian",
        ]
    )

    # Augment the app config with some extra attributes
    first_app_config.surprise_0 = "AAAA"
    first_app_config.surprise_1 = "BBBB"
    first_app_config.surprise_2 = "CCCC"
    first_app_config.surprise_3 = "DDDD"

    first_app_config.debian = {
        "surprise_1": "1111",
        "surprise_2": "1112",
        "surprise_3": "1113",
    }
    first_app_config.somevendor = {
        "surprise_2": "2222",
        "surprise_3": "2223",
        # A version config that will be ignored
        "normal": {
            "surprise_1": "XXXX",
        },
    }
    # A different vendor and version that will be ignored
    first_app_config.ubuntu = {
        "surprise_1": "YYYY",
        "jammy": {
            "surprise_1": "ZZZZ",
        },
    }

    create_command.finalize_app_config(first_app_config)

    # The target's config attributes have been merged into the app
    # Base app properties that aren't overwritten persist
    assert first_app_config.surprise_0 == "AAAA"
    # Properties can be overwritten at the base vendor level
    assert first_app_config.surprise_1 == "1111"
    # Properties can be overwritten at the vendor level
    assert first_app_config.surprise_2 == "2222"
    assert first_app_config.surprise_3 == "2223"

    # The glibc version was determined
    assert first_app_config.glibc_version == "2.42"

    # Since it's system python, the python version is 3
    assert first_app_config.python_version_tag == "3"


def test_passive_mixin(first_app_config, tmp_path):
    """An app using the PassiveMixin can be finalized."""
    run_command = LinuxSystemRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    # Build the app without docker
    run_command.target_image = None
    run_command.target_glibc_version = MagicMock(return_value="2.42")

    os_release = "\n".join(
        [
            "ID=somevendor",
            "VERSION_CODENAME=surprising",
            "ID_LIKE=debian",
        ]
    )
    if sys.version_info >= (3, 10):
        # mock platform.freedesktop_os_release()
        run_command.tools.platform.freedesktop_os_release = MagicMock(
            return_value=parse_freedesktop_os_release(os_release)
        )
    else:
        # For Pre Python3.10, mock the /etc/release file
        create_file(tmp_path / "os-release", os_release)
        run_command.tools.ETC_OS_RELEASE = tmp_path / "os-release"

    # Finalize the app config
    run_command.finalize_app_config(first_app_config)

    # The app's image, vendor and codename have been constructed from the target image
    assert first_app_config.target_image == "somevendor:surprising"
    assert first_app_config.target_vendor == "somevendor"
    assert first_app_config.target_codename == "surprising"
    assert first_app_config.target_vendor_base == "debian"

    # For tests of other properties merged in finalization, see
    # test_properties
