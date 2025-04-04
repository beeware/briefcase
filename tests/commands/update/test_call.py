import pytest

from briefcase.commands.create import Git
from briefcase.exceptions import BriefcaseCommandError


def test_no_git(update_command, monkeypatch):
    """If Git is not installed, an error is raised."""

    def monkeypatch_verify_git(*a, **kw):
        raise BriefcaseCommandError("Briefcase requires git, but it is not installed")

    monkeypatch.setattr(Git, "verify", monkeypatch_verify_git)

    # The command will fail tool verification.
    with pytest.raises(
        BriefcaseCommandError, match=r"Briefcase requires git, but it is not installed"
    ):
        update_command()


def test_update(update_command, first_app, second_app):
    """The update command can be called."""
    # Configure no command line options
    options, _ = update_command.parse_options([])

    update_command(**options)

    # The right sequence of things will be done
    assert update_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update the first app
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("cleanup", "first"),
        # Update the second app
        ("verify-app-template", "second"),
        ("verify-app-tools", "second"),
        ("code", "second", False),
        ("cleanup", "second"),
    ]


def test_update_single(update_command, first_app, second_app):
    """The update command can be called to update a single app from the config."""
    # Configure no command line options
    options, _ = update_command.parse_options([])

    update_command(app=update_command.apps["first"], **options)

    # The right sequence of things will be done
    assert update_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # Update the first app
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("cleanup", "first"),
    ]


def test_update_with_requirements(update_command, first_app, second_app):
    """The update command can be called, requesting a requirements update."""
    # Configure a requirements update
    options, _ = update_command.parse_options(["-r"])

    update_command(**options)

    # The right sequence of things will be done
    assert update_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update the first app
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("requirements", "first", False),
        ("cleanup", "first"),
        # Update the second app
        ("verify-app-template", "second"),
        ("verify-app-tools", "second"),
        ("code", "second", False),
        ("requirements", "second", False),
        ("cleanup", "second"),
    ]


def test_update_with_resources(update_command, first_app, second_app):
    """The update command can be called, requesting a resources update."""
    # Configure no command line options
    options, _ = update_command.parse_options(["--update-resources"])

    update_command(**options)

    # The right sequence of things will be done
    assert update_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update the first app
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("resources", "first"),
        ("cleanup", "first"),
        # Update the second app
        ("verify-app-template", "second"),
        ("verify-app-tools", "second"),
        ("code", "second", False),
        ("resources", "second"),
        ("cleanup", "second"),
    ]


def test_update_with_support(update_command, first_app, second_app):
    """The update command can be called, requesting an app support update."""
    # Configure no command line options
    options, _ = update_command.parse_options(["--update-support"])

    update_command(**options)

    # The right sequence of things will be done
    assert update_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update the first app
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("cleanup-support", "first"),
        ("support", "first"),
        ("cleanup", "first"),
        # Update the second app
        ("verify-app-template", "second"),
        ("verify-app-tools", "second"),
        ("code", "second", False),
        ("cleanup-support", "second"),
        ("support", "second"),
        ("cleanup", "second"),
    ]


# Parametrize both --apps/-a flags
@pytest.mark.parametrize("app_flags", ["--app", "-a"])
def test_update_app_single(update_command, first_app, second_app, app_flags):
    """If the --app or -a flag is used, only the selected app is updated."""
    # Configure command line options with the parameterized flag
    options, _ = update_command.parse_options([app_flags, "first"])

    # Run the update command
    update_command(**options)

    # Only the selected app is updated
    assert update_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update the app
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("cleanup", "first"),
    ]


def test_update_app_invalid(update_command, first_app, second_app):
    """If an invalid app name is passed to --app, raise an error."""
    # Add two apps
    update_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure the --app option with an invalid app
    options, _ = update_command.parse_options(["--app", "invalid"])

    # Running the command should raise an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"App 'invalid' does not exist in this project.",
    ):
        update_command(**options)


def test_update_app_none_defined(update_command):
    """If no apps are defined, do nothing."""
    # No apps defined
    update_command.apps = {}

    # Configure no command line options
    options, _ = update_command.parse_options([])

    # Run the update command
    result = update_command(**options)

    # The right sequence of things will be done
    assert result is None
    assert update_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
    ]


def test_update_app_all_flags(update_command, first_app, second_app):
    """Verify that all update-related flags work correctly with -a."""
    options, _ = update_command.parse_options(
        [
            "-a",
            "first",
            "--update-requirements",
            "--update-resources",
            "--update-support",
            "--update-stub",
            "--no-input",
            "--log",
            "-vv",
        ]
    )

    # Run the update command
    update_command(**options)

    # The right sequence of things will be done
    assert update_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # Update the app
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("code", "first", False),
        ("requirements", "first", False),
        ("resources", "first"),
        ("cleanup-support", "first"),
        ("support", "first"),
        ("cleanup", "first"),
    ]
