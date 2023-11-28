import pytest

from briefcase.config import AppConfig
from briefcase.exceptions import UnsupportedPlatform


def test_create_app(tracking_create_command, tmp_path):
    """If the app doesn't already exist, it will be created."""
    tracking_create_command.create_app(tracking_create_command.apps["first"])

    # Input wasn't required by the user
    assert tracking_create_command.input.prompts == []

    # The right sequence of things will be done
    assert tracking_create_command.actions == [
        ("generate", "first"),
        ("support", "first"),
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("requirements", "first", False),
        ("resources", "first"),
        ("cleanup", "first"),
    ]

    # New app content has been created
    assert (tmp_path / "base_path/build/first/tester/dummy/new").exists()


def test_create_existing_app_overwrite(tracking_create_command, tmp_path):
    """An existing app can be overwritten if requested."""
    # Answer yes when asked
    tracking_create_command.input.values = ["y"]

    # Generate an app in the location.
    bundle_path = tmp_path / "base_path/build/first/tester/dummy"
    bundle_path.mkdir(parents=True)
    with (bundle_path / "original").open("w", encoding="utf-8") as f:
        f.write("original template!")

    tracking_create_command.create_app(tracking_create_command.apps["first"])

    # Input was required by the user
    assert tracking_create_command.input.prompts == [
        "Application 'first' already exists; overwrite [y/N]? "
    ]

    # The right sequence of things will be done
    assert tracking_create_command.actions == [
        ("generate", "first"),
        ("support", "first"),
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("requirements", "first", False),
        ("resources", "first"),
        ("cleanup", "first"),
    ]

    # Original content has been deleted
    assert not (bundle_path / "original").exists()

    # New app content has been created
    assert (bundle_path / "new").exists()


def test_create_existing_app_no_overwrite(tracking_create_command, tmp_path):
    """If you say no, the existing app won't be overwritten."""
    # Answer no when asked
    tracking_create_command.input.values = ["n"]

    bundle_path = tmp_path / "base_path/build/first/tester/dummy"
    bundle_path.mkdir(parents=True)
    with (bundle_path / "original").open("w", encoding="utf-8") as f:
        f.write("original template!")
    tracking_create_command.create_app(tracking_create_command.apps["first"])

    # Input was required by the user
    assert tracking_create_command.input.prompts == [
        "Application 'first' already exists; overwrite [y/N]? "
    ]

    # No app creation actions will be performed
    assert tracking_create_command.actions == []

    # Original content still exists
    assert (bundle_path / "original").exists()

    # New app content has not been created
    assert not (bundle_path / "new").exists()


def test_create_existing_app_no_overwrite_default(tracking_create_command, tmp_path):
    """By default, the existing app won't be overwritten."""
    # Answer '' (i.e., just press return) when asked
    tracking_create_command.input.values = [""]

    bundle_path = tmp_path / "base_path/build/first/tester/dummy"
    bundle_path.mkdir(parents=True)
    with (bundle_path / "original").open("w", encoding="utf-8") as f:
        f.write("original template!")

    tracking_create_command.create_app(tracking_create_command.apps["first"])

    # Input was required by the user
    assert tracking_create_command.input.prompts == [
        "Application 'first' already exists; overwrite [y/N]? "
    ]

    # And no actions were necessary
    assert tracking_create_command.actions == []

    # Original content still exists
    assert (bundle_path / "original").exists()

    # New app content has not been created
    assert not (bundle_path / "new").exists()


def test_create_existing_app_input_disabled(tracking_create_command, tmp_path):
    """If input is disabled, fallback to default without get input from user."""
    # Answer '' (i.e., just press return) when asked
    tracking_create_command.input.enabled = False

    bundle_path = tmp_path / "base_path/build/first/tester/dummy"
    bundle_path.mkdir(parents=True)
    with (bundle_path / "original").open("w", encoding="utf-8") as f:
        f.write("original template!")

    tracking_create_command.create_app(tracking_create_command.apps["first"])

    # Input wasn't required by the user
    assert tracking_create_command.input.prompts == []

    # And no actions were necessary
    assert tracking_create_command.actions == []

    # Original content still exists
    assert (bundle_path / "original").exists()

    # New app content has not been created
    assert not (bundle_path / "new").exists()


def test_create_app_not_supported(tracking_create_command, tmp_path):
    """If the supported attribute is false, the command will terminate with an error
    message."""

    with pytest.raises(UnsupportedPlatform):
        tracking_create_command.create_app(
            AppConfig(
                app_name="third",
                bundle="com.example",
                version="0.0.3",
                description="The third simple app",
                sources=["src/third"],
                supported=False,
            )
        )

    # No actions carried out
    assert tracking_create_command.actions == []
