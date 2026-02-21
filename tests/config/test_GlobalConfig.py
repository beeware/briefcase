import pytest
from packaging.version import Version

from briefcase.config import GlobalConfig
from briefcase.exceptions import BriefcaseConfigError

# Examples of valid versions; input, parsed
VALID_VERSIONS = [
    ("1", "1"),  # Single digit
    ("1.0", "1.0"),  # Two digits
    ("1.2.3", "1.2.3"),  # Semver digits
    ("1.2.3.4", "1.2.3.4"),  # Keep going...
    ("v1.2.3", "1.2.3"),  # v prefix
    ("V1.2.3", "1.2.3"),  # v prefix, capitalized
    ("2025.9.5", "2025.9.5"),  # Calver
    ("2025.09.05", "2025.09.05"),  # Calver with leading zero
    ("1.2.3.dev42", "1.2.3.dev42"),  # dev
    ("1.2.3a42", "1.2.3a42"),  # alpha
    ("1.2.3b42", "1.2.3b42"),  # beta
    ("1.2.3rc42", "1.2.3rc42"),  # release candidate
    ("1.2.3.post42", "1.2.3post42"),  # post release
    ("1.2.3.post37.dev42", "1.2.3post37.dev42"),  # dev post release
    ("1.2.3.DEV42", "1.2.3.dev42"),  # dev, capitalized
    ("1.2.3A42", "1.2.3a42"),  # alpha, capitalized
    ("1.2.3B42", "1.2.3b42"),  # beta, capitalized
    ("1.2.3RC42", "1.2.3rc42"),  # release candidate, capitalized
    ("1.2.3.POST42", "1.2.3post42"),  # post release, capitalized
    ("1.2.3alpha42", "1.2.3a42"),  # alpha, full spelling
    ("1.2.3beta42", "1.2.3b42"),  # beta, full spelling
    ("1.2.3c42", "1.2.3rc42"),  # release candidate, alternate spelling
    ("1.2.3pre42", "1.2.3rc42"),  # release candidate, alternate spelling
    ("1.2.3preview42", "1.2.3rc42"),  # release candidate, alternate spelling
    ("1.2.3-42", "1.2.3post42"),  # post release, alternate spelling
    ("1.2.3-r42", "1.2.3post42"),  # post release, alternate spelling
    ("1.2.3a", "1.2.3a0"),  # implied alpha version
    ("1.2.3b", "1.2.3b0"),  # implied beta version
    ("1.2.3rc", "1.2.3rc0"),  # implied release candidate version
    ("1.2.3.post", "1.2.3.post"),  # implied post-release version
    ("1.2.3a05", "1.2.3a5"),  # leading zero trimming in postversion digits
    ("1.2.3-dev5", "1.2.3.dev5"),  # hyphen in postversion digits
    ("1.2.3_dev5", "1.2.3.dev5"),  # underscore in postversion digits
    ("1.2.3a-5", "1.2.3a5"),  # hyphen and letter in postversion digits
    ("1.2.3a_5", "1.2.3a5"),  # underscore and letter in postversion digits
    ("2!1.2.3", "2!1.2.3"),  # Epoch
    ("1.2.3+ubuntu.1", "1.2.3+ubuntu.1"),  # Local version segment
    (
        "v2!1.2.3rc37.post42+ubuntu.1",
        "2!1.2.3rc37.post42+ubuntu.1",
    ),  # all the options
    (Version("1.2.3"), "1.2.3"),  # Version object as input
]


def test_minimal_GlobalConfig():
    """A simple config can be defined."""
    config = GlobalConfig(
        project_name="My Project",
        version="1.2.3",
        bundle="org.beeware",
        license={"file": "LICENSE"},
    )

    # The basic properties have been set.
    assert config.project_name == "My Project"
    assert config.version == Version("1.2.3")
    assert config.bundle == "org.beeware"

    assert repr(config) == "<My Project v1.2.3 GlobalConfig>"


def test_extra_attrs():
    """A config can contain attributes in addition to those required."""
    config = GlobalConfig(
        project_name="My Project",
        version="1.2.3",
        bundle="org.beeware",
        url="https://example.com",
        author="Jane Smith",
        author_email="jane@example.com",
        first="value 1",
        second=42,
        license={"file": "LICENSE"},
    )

    # The basic properties have been set.
    assert config.project_name == "My Project"
    assert config.version == Version("1.2.3")
    assert config.bundle == "org.beeware"
    assert config.url == "https://example.com"
    assert config.author == "Jane Smith"
    assert config.author_email == "jane@example.com"

    # Explicit additional properties have been set
    assert config.first == "value 1"
    assert config.second == 42

    # An attribute that wasn't provided raises an error
    with pytest.raises(AttributeError):
        _ = config.unknown


@pytest.mark.parametrize(("input", "expected"), VALID_VERSIONS)
def test_valid_app_version(input, expected):
    config = GlobalConfig(
        project_name="My Project",
        version=input,
        bundle="org.beeware",
        license={"file": "LICENSE"},
    )

    assert config.version == Version(expected)


def test_invalid_app_version():
    with pytest.raises(
        BriefcaseConfigError, match=r"Version number \(foobar\) is not valid\."
    ):
        GlobalConfig(
            project_name="My Project",
            version="foobar",
            bundle="org.beeware",
            license={"file": "LICENSE"},
        )
