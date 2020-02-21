import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_git(build_command):
    "If Git is not installed, an error is raised"
    # Mock a non-existent git
    build_command.git = None

    # The command will fail tool verification.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires git, but it is not installed"
    ):
        build_command()


def test_specific_app(build_command, first_app, second_app):
    "If a specific app is requested, build it"
    # Add two apps
    build_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure no command line options
    options = build_command.parse_options([])

    # Run the build command
    build_command(first_app, **options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Build the first app; no state
        ('build', 'first', {'verbosity': 1}),
    ]


def test_multiple_apps(build_command, first_app, second_app):
    "If there are multiple apps, build all of them"
    # Add two apps
    build_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure no command line options
    options = build_command.parse_options([])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Build the first app; no state
        ('build', 'first', {'verbosity': 1}),

        # Build the second apps; state from previous build.
        ('build', 'second', {'verbosity': 1, 'build_state': 'first'}),
    ]


def test_non_existent(build_command, first_app_config, second_app):
    "Requesting a build of a non-existent app causes a create"
    # Add two apps; use the "config only" version of the first app.
    build_command.apps = {
        'first': first_app_config,
        'second': second_app,
    }

    # Configure no command line options
    options = build_command.parse_options([])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # First App doesn't exist, so it will be created, then built
        ('create', 'first', {'verbosity': 1}),
        ('build', 'first', {'verbosity': 1, 'create_state': 'first'}),

        # Second app *does* exist, so it only be built
        ('build', 'second', {'verbosity': 1, 'create_state': 'first', 'build_state': 'first'}),
    ]


def test_unbuilt(build_command, first_app_unbuilt, second_app):
    "Requesting a build of an app that has been created, but not build, just causes a build"
    # Add two apps; use the "unbuilt" version of the first app.
    build_command.apps = {
        'first': first_app_unbuilt,
        'second': second_app,
    }

    # Configure no command line options
    options = build_command.parse_options([])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # First App exists, but hasn't been built; it will be built.
        ('build', 'first', {'verbosity': 1}),

        # Second app has been built before; it will be built again.
        ('build', 'second', {'verbosity': 1, 'build_state': 'first'}),
    ]


def test_update_app(build_command, first_app, second_app):
    "If an update is requested, app is updated before build"
    # Add two apps
    build_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure a -a command line option
    options = build_command.parse_options(['-u'])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Update then build the first app
        ('update', 'first', {'verbosity': 1}),
        ('build', 'first', {'verbosity': 1, 'update_state': 'first'}),

        # Update then build the second app
        ('update', 'second', {'verbosity': 1, 'update_state': 'first', 'build_state': 'first'}),
        ('build', 'second', {'verbosity': 1, 'update_state': 'second', 'build_state': 'first'}),
    ]


def test_update_non_existent(build_command, first_app_config, second_app):
    "Requesting an update of a non-existent app causes a create"
    # Add two apps; use the "config only" version of the first app.
    build_command.apps = {
        'first': first_app_config,
        'second': second_app,
    }

    # Configure no command line options
    options = build_command.parse_options(['-u'])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # First App doesn't exist, so it will be created, then built
        ('create', 'first', {'verbosity': 1}),
        ('build', 'first', {'verbosity': 1, 'create_state': 'first'}),

        # Second app *does* exist, so it will be updated, then built
        ('update', 'second', {'verbosity': 1, 'create_state': 'first', 'build_state': 'first'}),
        ('build', 'second', {
            'verbosity': 1,
            'create_state': 'first',
            'build_state': 'first',
            'update_state': 'second'
        }),
    ]


def test_update_unbuilt(build_command, first_app_unbuilt, second_app):
    "Requesting an update of an upbuilt app causes an update before build"
    # Add two apps; use the "unbuilt" version of the first app.
    build_command.apps = {
        'first': first_app_unbuilt,
        'second': second_app,
    }

    # Configure no command line options
    options = build_command.parse_options(['-u'])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # First App exists, but hasn't been built; it will updated then built.
        ('update', 'first', {'verbosity': 1}),
        ('build', 'first', {'verbosity': 1, 'update_state': 'first'}),

        # Second app has been built before; it will be built again.
        ('update', 'second', {'verbosity': 1, 'update_state': 'first', 'build_state': 'first'}),
        ('build', 'second', {'verbosity': 1, 'update_state': 'second', 'build_state': 'first'}),
    ]
