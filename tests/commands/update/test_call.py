import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_git(update_command):
    "If Git is not installed, an error is raised"
    # Mock a non-existent git
    update_command.git = None

    # The command will fail tool verification.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires git, but it is not installed"
    ):
        update_command()


def test_update(update_command, first_app, second_app):
    "The update command can be called"
    # Configure no command line options
    options = update_command.parse_options([])

    update_command(**options)

    # The right sequence of things will be done
    assert update_command.actions == [
        ('verify'),

        # Update the first app
        ('code', update_command.apps['first']),

        # Update the second app
        ('code', update_command.apps['second']),
    ]


def test_update_single(update_command, first_app, second_app):
    "The update command can be called to update a single app from the config"
    # Configure no command line options
    options = update_command.parse_options([])

    update_command(app=update_command.apps['first'], **options)

    # The right sequence of things will be done
    assert update_command.actions == [
        ('verify'),

        # update the first app
        ('code', update_command.apps['first']),
    ]


def test_update_with_dependencies(update_command, first_app, second_app):
    "The update command can be called, requesting a dependencies update"
    # Configure no command line options
    options = update_command.parse_options(['-d'])

    update_command(**options)

    # The right sequence of things will be done
    assert update_command.actions == [
        ('verify'),

        # Update the first app
        ('dependencies', update_command.apps['first']),
        ('code', update_command.apps['first']),

        # Update the second app
        ('dependencies', update_command.apps['second']),
        ('code', update_command.apps['second']),
    ]


def test_update_with_resources(update_command, first_app, second_app):
    "The update command can be called, requesting a resources update"
    # Configure no command line options
    options = update_command.parse_options(['-r'])

    update_command(**options)

    # The right sequence of things will be done
    assert update_command.actions == [
        ('verify'),

        # Update the first app
        ('code', update_command.apps['first']),
        ('resources', update_command.apps['first']),

        # Update the second app
        ('code', update_command.apps['second']),
        ('resources', update_command.apps['second']),
    ]
