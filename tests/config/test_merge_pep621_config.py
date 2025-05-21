from unittest.mock import Mock

import pytest

from briefcase.config import merge_pep621_config
from briefcase.exceptions import BriefcaseConfigError


def test_empty():
    "Merging a PEP621 config with no interesting keys causes no changes"
    briefcase_config = {"key": "value"}

    merge_pep621_config(briefcase_config, {"other": "thingy"}, console=Mock())

    assert briefcase_config == {"key": "value"}


def test_base_keys():
    "If the PEP621 config provides keys, they are added"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {
            "description": "It's cool",
            "version": "1.2.3",
            "urls": {"Homepage": "https://example.com"},
            "license": {"text": "BSD License"},
            "requires-python": ">=3.9",
        },
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "description": "It's cool",
        "version": "1.2.3",
        "license": {"text": "BSD License"},
        "url": "https://example.com",
        "requires_python": ">=3.9",
    }


def test_base_keys_override():
    "If the PEP621 config provides keys, they are added"
    briefcase_config = {
        "key": "value",
        "description": "Good code I promise",
        "version": "2.3.4",
        "url": "https://beeware.org",
        "license": "BSD License",
    }

    merge_pep621_config(
        briefcase_config,
        {
            "description": "It's cool",
            "version": "1.2.3",
            "urls": {"Homepage": "https://example.com"},
            "license": {"text": "GPL3"},
        },
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "description": "Good code I promise",
        "version": "2.3.4",
        "license": "BSD License",
        "url": "https://beeware.org",
    }


def test_missing_subkeys():
    "If a subkey is missing, the value is ignored"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {
            "urls": {"Sponsorship": "https://example.com"},
        },
        console=Mock(),
    )

    assert briefcase_config == {"key": "value"}


def test_specified_license_file_pep621():
    "The license file is included in the briefcase config if specified in the PEP621 config"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {
            "license": {"file": "license.txt"},
        },
        console=Mock(),
    )

    assert briefcase_config == {"key": "value", "license": {"file": "license.txt"}}


@pytest.fixture
def dir_with_license(tmp_path):
    (tmp_path / "LICENSE").write_text("LICENSE", encoding="utf-8")
    (tmp_path / "AUTHORS").write_text("AUTHORS", encoding="utf-8")
    return tmp_path.absolute()


@pytest.mark.parametrize(
    "pep621_config",
    [
        pytest.param({"license-files": ["LICENSE"]}, id="single_existing_file"),
        pytest.param(
            {"license-files": ["LICENSE", "NON_EXISTING"]}, id="many_files_first_exists"
        ),
        pytest.param(
            {"license-files": ["LICENSE", "AUTHORS"]}, id="many_files_all_exists"
        ),
        pytest.param(
            {"license-files": ["NON_EXISTING", "LICENSE"]}, id="many_files_last_exists"
        ),
        pytest.param({"license-files": ["LICEN[SC]E"]}, id="glob_pattern"),
    ],
)
@pytest.mark.parametrize(
    "briefcase_config",
    [
        pytest.param({"key": "value"}, id="without_briefcase_license_file"),
        pytest.param(
            {"key": "value", "license": {"file": "OLD_LICENSE"}},
            id="with_briefcase_license_file",
        ),
    ],
)
def test_first_specified_license_file_pep639(
    pep621_config, briefcase_config, dir_with_license
):
    """The first file in license-files is used if no license in briefcase_config"""
    briefcase_config = briefcase_config.copy()
    pep621_config = pep621_config.copy()
    supposed_license = "LICENSE"
    if "license" in briefcase_config:
        supposed_license = briefcase_config["license"]["file"]

    merge_pep621_config(
        briefcase_config, pep621_config, console=Mock(), cwd=dir_with_license
    )
    assert briefcase_config == {"key": "value", "license": {"file": supposed_license}}


def test_specified_license_file_doesnt_exist_pep639_fails():
    """An exception is raised if no license file match the 'license-files' glob"""
    pep621_config = {"license-files": ["NON_EXISTING"]}
    with pytest.raises(BriefcaseConfigError):
        merge_pep621_config({}, pep621_config, console=Mock())


def test_more_than_one_license_file_pep639_warns(dir_with_license):
    """A warning is shown if multiple license files match the 'license-files' glob"""
    (dir_with_license / "AUTHORS").write_text("AUTHORS", encoding="utf-8")
    pep621_config = {"license-files": ["LICEN[SC]E", "AUTHORS"]}
    mock_console = Mock()
    merge_pep621_config({}, pep621_config, console=mock_console)


def test_both_license_file_and_license_dict(dir_with_license):
    """An error is raised if the license-files field is set and license is a dict

    PEP639 specifies that an exception MUST be raised if the license-files attribute
    is set while the license field is a dict.
    """
    (dir_with_license / "LICENSE").write_text("", encoding="utf-8")
    pep621_config = {
        "license-files": ["LICEN[SC]E", "AUTHORS"],
        "license": {"file": "LICENSE"},
    }
    mock_console = Mock()
    with pytest.raises(BriefcaseConfigError):
        merge_pep621_config({}, pep621_config, console=mock_console)


def test_empty_authors():
    "If the author list is empty, no author is recorded"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {"authors": []},
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
    }


def test_single_author():
    "If there is a single author, their details are recorded"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {
            "authors": [
                {
                    "name": "Jane Developer",
                    "email": "jane@example.com",
                }
            ]
        },
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "author": "Jane Developer",
        "author_email": "jane@example.com",
    }


def test_multiple_authors():
    "If there are multiple authors, the first author is recorded"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {
            "authors": [
                {
                    "name": "Jane Developer",
                    "email": "jane@example.com",
                },
                {
                    "name": "John Assistant",
                    "email": "john@somewhere.com",
                },
            ]
        },
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "author": "Jane Developer",
        "author_email": "jane@example.com",
    }


def test_mising_author_name():
    "If the author is missing name, only the author email is captured"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {
            "authors": [
                {
                    "email": "jane@example.com",
                }
            ]
        },
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "author_email": "jane@example.com",
    }


def test_missing_author_email():
    "If the author email is missing, the name is still recorded"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {
            "authors": [
                {
                    "name": "Jane Developer",
                }
            ]
        },
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "author": "Jane Developer",
    }


def test_existing_author_name():
    "If the author is defined in the global config, the PEP621 value is ignored"
    briefcase_config = {"key": "value", "author": "Grace Hopper"}

    merge_pep621_config(
        briefcase_config,
        {
            "authors": [
                {
                    "name": "Jane Developer",
                    "email": "jane@example.com",
                }
            ]
        },
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "author": "Grace Hopper",
        "author_email": "jane@example.com",
    }


def test_existing_author_email():
    "If the author email is missing, the name is still recorded"
    briefcase_config = {"key": "value", "author_email": "grace@hopper.org"}

    merge_pep621_config(
        briefcase_config,
        {
            "authors": [
                {
                    "name": "Jane Developer",
                    "email": "jane@example.com",
                }
            ]
        },
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "author": "Jane Developer",
        "author_email": "grace@hopper.org",
    }


def test_no_dependencies():
    "If there are no global dependencies, requires are used as is."
    briefcase_config = {"key": "value", "requires": ["first", "second"]}

    merge_pep621_config(
        briefcase_config,
        {},
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "requires": ["first", "second"],
    }


def test_dependencies_without_requires():
    "If the global config doesn't specify requirements, dependencies are used as is"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {"dependencies": ["dep1", "dep2"]},
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "requires": ["dep1", "dep2"],
    }


def test_dependencies_with_requires():
    "If the global config specify requirements, requires augments dependencies"
    briefcase_config = {"key": "value", "requires": ["first", "second"]}

    merge_pep621_config(
        briefcase_config,
        {"dependencies": ["dep1", "dep2"]},
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "requires": ["dep1", "dep2", "first", "second"],
    }


def test_no_test_dependencies():
    "If the global config doesn't specify test dependencies, test_requires are used as is"
    briefcase_config = {"key": "value", "test_requires": ["first", "second"]}

    merge_pep621_config(
        briefcase_config,
        {},
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "test_requires": ["first", "second"],
    }


def test_optional_non_test_dependencies():
    "If the global config has non-test optional requirements, requires is used as-is"
    briefcase_config = {"key": "value", "requires": ["first", "second"]}

    merge_pep621_config(
        briefcase_config,
        {"optional-dependencies": {"other": ["dep1", "dep2"]}},
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "requires": ["first", "second"],
    }


def test_test_dependencies_without_requires():
    "If the global config doesn't specify test requirements, test dependencies are used as is"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {"optional-dependencies": {"test": ["dep1", "dep2"]}},
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "test_requires": ["dep1", "dep2"],
    }


def test_test_dependencies_with_requires():
    "If the global config specify requirements, requires augments dependencies"
    briefcase_config = {"key": "value", "test_requires": ["first", "second"]}

    merge_pep621_config(
        briefcase_config,
        {"optional-dependencies": {"test": ["dep1", "dep2"]}},
        console=Mock(),
    )

    assert briefcase_config == {
        "key": "value",
        "test_requires": ["dep1", "dep2", "first", "second"],
    }
