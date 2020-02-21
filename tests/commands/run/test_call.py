import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_git(run_command):
    "If Git is not installed, an error is raised"
    # Mock a non-existent git
    run_command.git = None

    # The command will fail tool verification.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires git, but it is not installed"
    ):
        run_command()


def test_no_args_one_app(run_command, first_app):
    "If there is one app, run starts that app by default"
    # Add a single app
    run_command.apps = {
        'first': first_app,
    }

    # Configure no command line options
    options = run_command.parse_options([])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Run the first app
        ('run', 'first', {'verbosity': 1}),
    ]


def test_no_args_two_apps(run_command, first_app, second_app):
    "If there are one app, run starts that app by default"
    # Add two apps
    run_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure no command line options
    options = run_command.parse_options([])

    # Invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        run_command(**options)

    # No actions will be performed
    assert run_command.actions == []


def test_with_arg_one_app(run_command, first_app):
    "If there is one app, and a -a argument, run starts that app"
    # Add a single app
    run_command.apps = {
        'first': first_app,
    }

    # Configure a -a command line option
    options = run_command.parse_options(['-a', 'first'])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Run the first app
        ('run', 'first', {'verbosity': 1}),
    ]


def test_with_arg_two_apps(run_command, first_app, second_app):
    "If there are multiple apps, the --app argument starts app nominated"
    # Add two apps
    run_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure a --app command line option
    options = run_command.parse_options(['--app', 'second'])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # Run the second app
        ('run', 'second', {'verbosity': 1}),
    ]


def test_bad_app_reference(run_command, first_app, second_app):
    "If the command line argument refers to an app that doesn't exist, raise an error"
    # Add two apps
    run_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure a --app command line option
    options = run_command.parse_options(['--app', 'does-not-exist'])

    # Invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        run_command(**options)

    # No actions will be performed
    assert run_command.actions == []


def test_create_app_before_start(run_command, first_app_config):
    "If the app to be started doesn't exist, create it first"
    # Add a single app, using the 'config only' fixture
    run_command.apps = {
        'first': first_app_config,
    }

    # Configure no command line options
    options = run_command.parse_options([])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # App doesn't exist, so it will be created and built
        ('create', 'first', {'verbosity': 1}),
        ('build', 'first', {'verbosity': 1, 'create_state': 'first'}),

        # Then, it will be started
        ('run', 'first', {'verbosity': 1, 'create_state': 'first', 'build_state': 'first'}),
    ]


def test_update_app(run_command, first_app):
    "The run command can request that the app is updated first"
    # Add a single app
    run_command.apps = {
        'first': first_app,
    }

    # Configure no command line options
    options = run_command.parse_options(['-u'])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # An update was requested
        ('update', 'first', {'verbosity': 1}),
        ('build', 'first', {'verbosity': 1, 'update_state': 'first'}),

        # Then, it will be started
        ('run', 'first', {'verbosity': 1, 'update_state': 'first', 'build_state': 'first'}),
    ]


def test_update_uncompiled_app(run_command, first_app_uncompiled):
    "The run command can request that an uncompiled app is updated first"
    # Add a single app
    run_command.apps = {
        'first': first_app_uncompiled,
    }

    # Configure no command line options
    options = run_command.parse_options(['-u'])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # An update was requested
        ('update', 'first', {'verbosity': 1}),
        ('build', 'first', {'verbosity': 1, 'update_state': 'first'}),

        # Then, it will be started
        ('run', 'first', {'verbosity': 1, 'update_state': 'first', 'build_state': 'first'}),
    ]


def test_update_non_existent(run_command, first_app_config):
    "Requesting an update of a non-existent app causes a create"
    # Add a single app, using the 'config only' fixture
    run_command.apps = {
        'first': first_app_config,
    }

    # Configure no command line options
    options = run_command.parse_options(['-u'])

    # Run the run command
    run_command(**options)

    # The right sequence of things will be done
    assert run_command.actions == [
        # App doesn't exist, so it will be created and built
        ('create', 'first', {'verbosity': 1}),
        ('build', 'first', {'verbosity': 1, 'create_state': 'first'}),

        # Then, it will be started
        ('run', 'first', {'verbosity': 1, 'create_state': 'first', 'build_state': 'first'}),
    ]
