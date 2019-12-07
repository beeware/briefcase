import pytest

from briefcase.config import GlobalConfig
from briefcase.exceptions import BriefcaseConfigError


def test_minimal_GlobalConfig():
    "A simple config can be defined"
    config = GlobalConfig(
        project_name="My Project",
        version="1.2.3",
        bundle="org.beeware",
    )

    # The basic properties have been set.
    assert config.project_name == "My Project"
    assert config.version == '1.2.3'
    assert config.bundle == 'org.beeware'

    assert repr(config) == "<My Project v1.2.3 GlobalConfig>"


def test_extra_attrs():
    "A config can contain attributes in addition to those required"
    config = GlobalConfig(
        project_name="My Project",
        version="1.2.3",
        bundle="org.beeware",
        url="https://example.com",
        author="Jane Smith",
        author_email="jane@example.com",
        first="value 1",
        second=42,
    )

    # The basic properties have been set.
    assert config.project_name == "My Project"
    assert config.version == '1.2.3'
    assert config.bundle == 'org.beeware'
    assert config.url == 'https://example.com'
    assert config.author == "Jane Smith"
    assert config.author_email == "jane@example.com"

    # Explicit additional properties have been set
    assert config.first == "value 1"
    assert config.second == 42

    # An attribute that wasn't provided raises an error
    with pytest.raises(AttributeError):
        config.unknown


def test_valid_app_version():
    try:
        GlobalConfig(
            project_name="My Project",
            version="1.2.3",
            bundle="org.beeware",
        )
    except BriefcaseConfigError:
        pytest.fail('1.2.3 should be a valid version number')


def test_invalid_app_version():
    with pytest.raises(BriefcaseConfigError, match=r"Version number \(foobar\) is not valid\."):
        GlobalConfig(
            project_name="My Project",
            version="foobar",
            bundle="org.beeware",
        )
