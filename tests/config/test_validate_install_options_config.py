import pytest

from briefcase.config import validate_install_options_config
from briefcase.exceptions import BriefcaseConfigError


@pytest.fixture
def option_config():
    return [
        {
            "name": "first",
            "title": "First option",
            "description": "Do the first thing",
            "default": True,
        },
        {
            "name": "second",
            "title": "Second option",
            "description": "Do the second thing",
            "default": False,
        },
        # An option that is alphabetically second, but appears third,
        # and has no explicit default.
        {
            "name": "default",
            "title": "Third option",
            "description": "Do the third thing",
        },
    ]


def test_no_install_options():
    """An config can have no install options."""
    assert validate_install_options_config(None) == {}


def test_install_options(option_config):
    """A config can provide installer options."""
    install_options = validate_install_options_config(option_config)

    assert install_options == {
        "first": {
            "title": "First option",
            "description": "Do the first thing",
            "default": True,
        },
        "second": {
            "title": "Second option",
            "description": "Do the second thing",
            "default": False,
        },
        "default": {
            "title": "Third option",
            "description": "Do the third thing",
            "default": False,
        },
    }


def test_missing_name(option_config):
    """Install options must provide a name."""
    del option_config[1]["name"]

    with pytest.raises(
        BriefcaseConfigError,
        match=r"Install option 1 does not define a `name`",
    ):
        validate_install_options_config(option_config)


def test_non_string(option_config):
    """Install option name must be a string."""
    option_config[1]["name"] = 42

    with pytest.raises(
        BriefcaseConfigError,
        match=r"Name for install option 1 is not a string",
    ):
        validate_install_options_config(option_config)


@pytest.mark.parametrize(
    "name",
    [
        "1option",
        "has space",
        "has+special&chars",
    ],
)
def test_identifier_name(option_config, name):
    """Install option names can't be identifiers."""
    option_config[1]["name"] = name
    with pytest.raises(
        BriefcaseConfigError,
        match=r"' cannot be used as an install option name",
    ):
        validate_install_options_config(option_config)


@pytest.mark.parametrize(
    "name",
    [
        "ALLUSERS",
        "AllUsers",
        "allusers",
    ],
)
def test_keyword_name(option_config, name):
    """Install option names can't be known keywords."""
    option_config[1]["name"] = name
    with pytest.raises(
        BriefcaseConfigError,
        match=r"' is a reserved install option identifier",
    ):
        validate_install_options_config(option_config)


@pytest.mark.parametrize(
    "name",
    [
        "first",
        "FiRsT",
        "FIRST",
    ],
)
def test_unique_name(option_config, name):
    """Install option names must be unique."""
    option_config[2]["name"] = name
    with pytest.raises(
        BriefcaseConfigError,
        match=r"Install option names must be unique.",
    ):
        validate_install_options_config(option_config)


def test_missing_title(option_config):
    """Install options must provide a title."""
    del option_config[1]["title"]
    with pytest.raises(
        BriefcaseConfigError,
        match=r"Install option 'second' does not provide a title.",
    ):
        validate_install_options_config(option_config)


def test_non_string_title(option_config):
    """Install options must provide a title."""
    option_config[1]["title"] = 42

    with pytest.raises(
        BriefcaseConfigError,
        match=r"Title for install option 'second' is not a string.",
    ):
        validate_install_options_config(option_config)


def test_missing_description(option_config):
    """Install options must provide a description."""
    del option_config[1]["description"]
    with pytest.raises(
        BriefcaseConfigError,
        match=r"Install option 'second' does not provide a description.",
    ):
        validate_install_options_config(option_config)


def test_non_string_description(option_config):
    """Install options must provide a string description."""
    option_config[1]["description"] = 42
    with pytest.raises(
        BriefcaseConfigError,
        match=r"Description for install option 'second' is not a string.",
    ):
        validate_install_options_config(option_config)
