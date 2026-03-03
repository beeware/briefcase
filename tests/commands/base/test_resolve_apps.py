import pytest

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError


@pytest.fixture
def first_app():
    return AppConfig(
        app_name="first",
        bundle="com.example",
        version="0.0.1",
        description="The first simple app",
        sources=["src/first"],
        license={"file": "LICENSE"},
    )


@pytest.fixture
def second_app():
    return AppConfig(
        app_name="second",
        bundle="com.example",
        version="0.0.2",
        description="The second simple app",
        sources=["src/second"],
        license={"file": "LICENSE"},
    )


def test_resolve_all_apps(base_command, first_app, second_app):
    """If no app or app_name is provided, all apps are returned."""
    base_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    result = base_command.resolve_apps()

    assert result == {"first": first_app, "second": second_app}


def test_resolve_by_app_name(base_command, first_app, second_app):
    """If app_name is provided, only that app is returned."""
    base_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    result = base_command.resolve_apps(app_name="first")

    assert result == {"first": first_app}


def test_resolve_by_app_config(base_command, first_app, second_app):
    """If an app config is provided, only that app is returned."""
    base_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    result = base_command.resolve_apps(app=first_app)

    assert result == {"first": first_app}


def test_resolve_invalid_app_name(base_command, first_app):
    """If an invalid app_name is provided, an error is raised."""
    base_command.apps = {
        "first": first_app,
    }

    with pytest.raises(
        BriefcaseCommandError,
        match=r"App 'invalid' does not exist in this project.",
    ):
        base_command.resolve_apps(app_name="invalid")


def test_app_name_takes_precedence_over_app(base_command, first_app, second_app):
    """If both app_name and app are provided, app_name takes precedence."""
    base_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    result = base_command.resolve_apps(app_name="first", app=second_app)

    assert result == {"first": first_app}
