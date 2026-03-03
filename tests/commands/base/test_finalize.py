import pytest

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseConfigError

from .conftest import DummyCommand


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


@pytest.fixture
def base_command(dummy_console, tmp_path, first_app, second_app):
    return DummyCommand(
        console=dummy_console,
        base_path=tmp_path,
        apps={
            "first": first_app,
            "second": second_app,
        },
    )


def test_finalize_all(base_command, first_app, second_app):
    "A call to finalize verifies host, tools, and finalized all app configs"
    base_command.finalize(apps=base_command.apps.values())

    # The right sequence of things will be done
    assert base_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App config has been finalized
        ("finalize-app-config", "second"),
    ]

    # Apps are no longer in draft mode
    assert not hasattr(first_app, "__draft__")
    assert not hasattr(second_app, "__draft__")


def test_finalize_single(base_command, first_app, second_app):
    "A call to finalize verifies host, tools, and finalizes a single app config"
    base_command.finalize(apps=[first_app])

    # The right sequence of things will be done
    assert base_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
    ]

    # First app is no longer in draft mode; second is
    assert not hasattr(first_app, "__draft__")
    assert hasattr(second_app, "__draft__")


def test_finalize_all_repeat(base_command, first_app, second_app):
    "Multiple calls to finalize verifies host & tools multiple times, but only once on config"
    # Finalize apps twice. This is an approximation of what happens
    # when a command chain is executed; create, update, build and run will
    # all finalize; create will finalize the app configs, each command will
    # have it's own tools verified.
    base_command.finalize(apps=base_command.apps.values())
    base_command.finalize(apps=base_command.apps.values())

    # The right sequence of things will be done
    assert base_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App config has been finalized
        ("finalize-app-config", "second"),
        # Host OS is verified again
        ("verify-host",),
        # Tools are verified again
        ("verify-tools",),
    ]

    # Apps are no longer in draft mode
    assert not hasattr(first_app, "__draft__")
    assert not hasattr(second_app, "__draft__")


def test_finalize_single_repeat(base_command, first_app, second_app):
    "Multiple calls to finalize verifies host & tools multiple times, but finalizes app config once"

    # Finalize app twice. This is an approximation of what happens
    # when a command chain is executed; create, update, build and run will
    # all finalize; create will finalize the app config, each command will
    # have it's own tools verified.
    base_command.finalize(apps=[first_app])
    base_command.finalize(apps=[first_app])

    # The right sequence of things will be done
    assert base_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # Host OS is verified again
        ("verify-host",),
        # Tools are verified again
        ("verify-tools",),
    ]

    # First app is no longer in draft mode; second is
    assert not hasattr(first_app, "__draft__")
    assert hasattr(second_app, "__draft__")


def test_external_and_internal(base_command, first_app):
    """If an app provides both sources and external_package_path, an error is raised."""
    first_app.external_package_path = "path/to/package"

    with pytest.raises(
        BriefcaseConfigError,
        match=r"'first' is declared as an external app, but also defines 'sources'",
    ):
        base_command.finalize(apps=[first_app])


def test_not_external_or_internal(base_command, first_app):
    """If an app provides neither sources or external_package_path, an error is
    raised."""
    first_app.sources = None

    with pytest.raises(
        BriefcaseConfigError,
        match=r"'first' does not define either 'sources' or 'external_package_path'.",
    ):
        base_command.finalize(apps=[first_app])


def test_binary_path_internal_app(base_command, first_app):
    """If an internal app defines external_package_executable_path, an error is
    raised."""
    first_app.external_package_executable_path = "internal/app.exe"

    with pytest.raises(
        BriefcaseConfigError,
        match=(
            r"'first' defines 'external_package_executable_path', "
            r"but not 'external_package_path'"
        ),
    ):
        base_command.finalize(apps=[first_app])
