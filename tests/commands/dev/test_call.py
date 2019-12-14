import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_args_one_app(dev_command, first_app):
    "If there is one app, dev starts that app by default"
    # Add a single app
    dev_command.apps = {
        'first': first_app,
    }

    # Configure no command line options
    options = dev_command.parse_options([])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # Run the first app devly
        ('run_dev', 'first', {'verbosity': 1}),
    ]


def test_no_args_two_apps(dev_command, first_app, second_app):
    "If there are one app, dev starts that app by default"
    # Add two apps
    dev_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure no command line options
    options = dev_command.parse_options([])

    # Invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        dev_command(**options)

    # No apps will be launched
    assert dev_command.actions == []


def test_with_arg_one_app(dev_command, first_app):
    "If there is one app, and a -a argument, dev starts that app"
    # Add a single app
    dev_command.apps = {
        'first': first_app,
    }

    # Configure a -a command line option
    options = dev_command.parse_options(['-a', 'first'])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # Run the first app devly
        ('run_dev', 'first', {'verbosity': 1}),
    ]


def test_with_arg_two_apps(dev_command, first_app, second_app):
    "If there are multiple apps, the --app argument starts app nominated"
    # Add two apps
    dev_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure a --app command line option
    options = dev_command.parse_options(['--app', 'second'])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # Run the second app devly
        ('run_dev', 'second', {'verbosity': 1}),
    ]


def test_bad_app_reference(dev_command, first_app, second_app):
    "If the command line argument refers to an app that doesn't exist, raise an error"
    # Add two apps
    dev_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure a --app command line option
    options = dev_command.parse_options(['--app', 'does-not-exist'])

    # Invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        dev_command(**options)

    # No apps will be launched
    assert dev_command.actions == []


def test_update_dependencies(dev_command, first_app):
    "The dev command can request that the app is updated first"
    # Add a single app
    dev_command.apps = {
        'first': first_app,
    }

    # Configure no command line options
    options = dev_command.parse_options(['-d'])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # An update was requested
        ('dev_dependencies', 'first', {'verbosity': 1}),

        # Then, it will be started
        ('run_dev', 'first', {'verbosity': 1}),
    ]


def test_run_uninstalled(dev_command, first_app_uninstalled):
    "The dev command will install first if the app hasn't been installed"
    # Add a single app
    dev_command.apps = {
        'first': first_app_uninstalled,
    }

    # Configure no command line options
    options = dev_command.parse_options([])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # The app will be installed
        ('dev_dependencies', 'first', {'verbosity': 1}),

        # Then, it will be started
        ('run_dev', 'first', {'verbosity': 1}),
    ]


def test_update_uninstalled(dev_command, first_app_uninstalled):
    "A request to update dependencies is redundant if the app hasn't been installed"
    # Add a single app
    dev_command.apps = {
        'first': first_app_uninstalled,
    }

    # Configure no command line options
    options = dev_command.parse_options(['-d'])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # An update was requested
        ('dev_dependencies', 'first', {'verbosity': 1}),

        # Then, it will be started
        ('run_dev', 'first', {'verbosity': 1}),
    ]
