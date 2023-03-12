import pytest

from briefcase.config import AppConfig

from .conftest import DummyCommand


@pytest.fixture
def first_app():
    return AppConfig(
        app_name="first",
        bundle="com.example",
        version="0.0.1",
        description="The first simple app",
        sources=["src/first"],
    )


@pytest.fixture
def second_app():
    return AppConfig(
        app_name="second",
        bundle="com.example",
        version="0.0.2",
        description="The second simple app",
        sources=["src/second"],
    )


@pytest.fixture
def base_command(tmp_path, first_app, second_app):
    return DummyCommand(
        base_path=tmp_path,
        apps={
            "first": first_app,
            "second": second_app,
        },
    )


def test_finalize_all(base_command, first_app, second_app):
    "A call to finalize verifies host, tools, and finalized all app configs"
    base_command.finalize()

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
    "A call to finalize verifies host, tools, and finalized all app configs"
    base_command.finalize(first_app)

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
    base_command.finalize()
    base_command.finalize()

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
    base_command.finalize(first_app)
    base_command.finalize(first_app)

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
