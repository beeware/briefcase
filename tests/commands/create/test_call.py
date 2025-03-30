import pytest

from briefcase.commands.create import Git
from briefcase.exceptions import BriefcaseCommandError


def test_no_git(tracking_create_command, monkeypatch):
    """If Git is not installed, an error is raised."""

    def monkeypatch_verify_git(*a, **kw):
        raise BriefcaseCommandError("Briefcase requires git, but it is not installed")

    monkeypatch.setattr(Git, "verify", monkeypatch_verify_git)

    # The command will fail tool verification.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires git, but it is not installed",
    ):
        tracking_create_command()


def test_create(tracking_create_command, tmp_path):
    """The create command can be called."""
    tracking_create_command()

    # The right sequence of things will be done
    assert tracking_create_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Create the first app
        ("generate", "first"),
        ("support", "first"),
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("requirements", "first", False),
        ("resources", "first"),
        ("cleanup", "first"),
        # Create the second app
        ("generate", "second"),
        ("support", "second"),
        ("verify-app-template", "second"),
        ("verify-app-tools", "second"),
        ("code", "second", False),
        ("requirements", "second", False),
        ("resources", "second"),
        ("cleanup", "second"),
    ]

    # New app content has been created
    assert (tmp_path / "base_path/build/first/tester/dummy/new").exists()
    assert (tmp_path / "base_path/build/second/tester/dummy/new").exists()


def test_create_single(tracking_create_command, tmp_path):
    """The create command can be called to create a single app from the config."""
    tracking_create_command(app=tracking_create_command.apps["first"])

    # The right sequence of things will be done
    assert tracking_create_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # Create the first app
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
    assert not (tmp_path / "base_path/build/second/tester/dummy/new").exists()


# Parametrize both --apps/-a flags
@pytest.mark.parametrize("app_flags", ["--app", "-a"])
def test_create_app_single(tracking_create_command, app_flags):
    """If the --app or -a flag is used, only the selected app is created."""
    # Configure command line options with the parameterized flag
    options, _ = tracking_create_command.parse_options([app_flags, "first"])

    # Run the create command
    tracking_create_command(**options)

    # Only the selected app is created
    assert tracking_create_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Create the selected app
        ("generate", "first"),
        ("support", "first"),
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("requirements", "first", False),
        ("resources", "first"),
        ("cleanup", "first"),
    ]


def test_create_app_invalid(tracking_create_command):
    """If an invalid app name is passed to --app, raise an error."""
    # Configure the --app option with an invalid app
    options, _ = tracking_create_command.parse_options(["--app", "invalid"])

    # Running the command should raise an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"App 'invalid' does not exist in this project.",
    ):
        tracking_create_command(**options)


def test_create_app_none_defined(tracking_create_command):
    """If no apps are defined, do nothing."""
    # No apps defined
    tracking_create_command.apps = {}

    # Configure no command line options
    options, _ = tracking_create_command.parse_options([])

    # Run the create command
    result = tracking_create_command(**options)

    # Nothing happens beyond basic setup
    assert result is None
    assert tracking_create_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
    ]


def test_create_app_all_flags(tracking_create_command):
    """Verify that all create-related flags work correctly with -a."""
    # Configure command line options with all available flags
    options, _ = tracking_create_command.parse_options(
        ["-a", "first", "--no-input", "--log", "-v"]
    )

    # Run the create command
    tracking_create_command(**options)

    # The right sequence of things will be done
    assert tracking_create_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Create the selected app
        ("generate", "first"),
        ("support", "first"),
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("requirements", "first", False),
        ("resources", "first"),
        ("cleanup", "first"),
    ]
