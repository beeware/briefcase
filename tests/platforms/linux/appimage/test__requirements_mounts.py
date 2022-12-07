import sys

import pytest

from briefcase.platforms.linux.appimage import LinuxAppImageMostlyPassiveMixin


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
@pytest.mark.parametrize(
    "requires, test_requires, mounts",
    [
        # No requirements or test requirements
        (None, None, []),
        (None, [], []),
        ([], None, []),
        ([], [], []),
        # No local requirements
        # Requirements, but not test requirements
        (["first", "second"], None, []),
        # Test Requirements, but no requirements
        (None, ["test_first", "test_second"], []),
        # Requirements, and test requirements
        (["first", "second"], ["test_first", "test_second"], []),
        # Local requirements in the mix
        # Requirements, but not test requirements
        (
            [
                "first",
                "/path/to/local1",
                "/path/to/local2",
                "second",
            ],
            None,
            [
                ("/path/to/local1", "/requirements/local1"),
                ("/path/to/local2", "/requirements/local2"),
            ],
        ),
        # Test Requirements, but no requirements
        (
            None,
            [
                "test_first",
                "/path/to/test_local1",
                "/path/to/test_local2",
                "test_second",
            ],
            [
                ("/path/to/test_local1", "/requirements/test_local1"),
                ("/path/to/test_local2", "/requirements/test_local2"),
            ],
        ),
        # Requirements, and test requirements
        (
            [
                "first",
                "/path/to/local1",
                "/path/to/local2",
                "second",
            ],
            [
                "test_first",
                "/path/to/test_local1",
                "/path/to/test_local2",
                "test_second",
            ],
            [
                ("/path/to/local1", "/requirements/local1"),
                ("/path/to/local2", "/requirements/local2"),
                ("/path/to/test_local1", "/requirements/test_local1"),
                ("/path/to/test_local2", "/requirements/test_local2"),
            ],
        ),
    ],
)
def test_requirements_mounts(first_app_config, requires, test_requires, mounts):
    command = LinuxAppImageMostlyPassiveMixin()

    first_app_config.requires = requires
    first_app_config.test_requires = test_requires

    assert command._requirements_mounts(first_app_config) == mounts
