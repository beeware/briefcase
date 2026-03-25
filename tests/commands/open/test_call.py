import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_open(open_command, first_app, second_app):
    """The open command can be called."""
    # Configure no command line options
    options, _ = open_command.parse_options([])

    open_command(**options)

    # The right sequence of things will be done
    assert open_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # open the first app
        ("open", "first"),
        # App template is verified
        ("verify-app-template", "second"),
        # App tools are verified
        ("verify-app-tools", "second"),
        # open the second app
        ("open", "second"),
    ]


def test_open_single(open_command, first_app):
    """The open command can be called to open a single app from the config."""
    # Configure no command line options
    options, _ = open_command.parse_options([])

    open_command(app=open_command.apps["first"], **options)

    # The right sequence of things will be done
    assert open_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # open the first app
        ("open", "first"),
    ]


def test_create_before_open(open_command, tmp_path):
    """If the app doesn't exist, it will be created before opening."""
    # Configure no command line options
    options, _ = open_command.parse_options([])

    open_command(app=open_command.apps["first"], **options)

    # The right sequence of things will be done
    assert open_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # create, then open the first app
        ("create", "first", {}),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        ("open", "first"),
    ]


def test_open_app_name(open_command, first_app, second_app):
    """The open command can be called with a specific app name."""
    # Configure the -a / --app command line option
    options, _ = open_command.parse_options(["-a", "first"])

    open_command(**options)

    # The right sequence of things will be done for ONLY the first app
    assert open_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # Selected app config has been finalized
        ("finalize-app-config", "first"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # open ONLY the first app
        ("open", "first"),
    ]


def test_open_app_invalid(open_command, first_app, second_app):
    """If an invalid app name is passed to --app, raise an error."""
    # Add two apps to the command
    open_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure the --app option with an invalid app
    options, _ = open_command.parse_options(["--app", "invalid"])

    # Running the command should raise an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"App 'invalid' does not exist in this project.",
    ):
        open_command(**options)


def test_open_app_none_defined(open_command):
    """If no apps are defined, do nothing."""
    # No apps defined in the project
    open_command.apps = {}

    # Configure no command line options
    options, _ = open_command.parse_options([])

    # Run the open command
    result = open_command(**options)

    # The command should return None and only verify host/tools
    assert result is None
    assert open_command.actions == [
        ("verify-host",),
        ("verify-tools",),
    ]
