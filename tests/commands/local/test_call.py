import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_args_one_app(local_command, first_app):
    "If there is one app, run starts that app by default"
    # Add a single app
    local_command.apps = {
        'first': first_app,
    }

    # Configure no command line options
    options = local_command.parse_options([])

    # Run the run command
    local_command(**options)

    # The right sequence of things will be done
    assert local_command.actions == [
        # Run the first app locally
        ('run_local', 'first', {'verbosity': 1}),
    ]


def test_no_args_two_apps(local_command, first_app, second_app):
    "If there are one app, run starts that app by default"
    # Add two apps
    local_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure no command line options
    options = local_command.parse_options([])

    # Invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        local_command(**options)

    # No apps will be launched
    assert local_command.actions == []


def test_with_arg_one_app(local_command, first_app):
    "If there is one app, and a -a argument, run starts that app"
    # Add a single app
    local_command.apps = {
        'first': first_app,
    }

    # Configure a -a command line option
    options = local_command.parse_options(['-a', 'first'])

    # Run the run command
    local_command(**options)

    # The right sequence of things will be done
    assert local_command.actions == [
        # Run the first app locally
        ('run_local', 'first', {'verbosity': 1}),
    ]


def test_with_arg_two_apps(local_command, first_app, second_app):
    "If there are multiple apps, the --app argument starts app nominated"
    # Add two apps
    local_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure a --app command line option
    options = local_command.parse_options(['--app', 'second'])

    # Run the run command
    local_command(**options)

    # The right sequence of things will be done
    assert local_command.actions == [
        # Run the second app locally
        ('run_local', 'second', {'verbosity': 1}),
    ]


def test_bad_app_reference(local_command, first_app, second_app):
    "If the command line argument refers to an app that doesn't exist, raise an error"
    # Add two apps
    local_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure a --app command line option
    options = local_command.parse_options(['--app', 'does-not-exist'])

    # Invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        local_command(**options)

    # No apps will be launched
    assert local_command.actions == []


def test_update_dependencies(local_command, first_app):
    "The run command can request that the app is updated first"
    # Add a single app
    local_command.apps = {
        'first': first_app,
    }

    # Configure no command line options
    options = local_command.parse_options(['-d'])

    # Run the run command
    local_command(**options)

    # The right sequence of things will be done
    assert local_command.actions == [
        # An update was requested
        # ('install_local_app_dependencies', 'first', {'verbosity': 1}),

        # Then, it will be started
        ('run_local', 'first', {'verbosity': 1}),
    ]
