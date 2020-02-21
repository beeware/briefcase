import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_git(publish_command):
    "If Git is not installed, an error is raised"
    # Mock a non-existent git
    publish_command.git = None

    # The command will fail tool verification.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires git, but it is not installed"
    ):
        publish_command()


def test_publish(publish_command, first_app, second_app):
    "If there are multiple apps, publish all of them"
    # Add two apps
    publish_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure no command line options
    options = publish_command.parse_options([])

    # Run the publish command
    publish_command(**options)

    # The right sequence of things will be done
    assert publish_command.actions == [
        # Publish the first app to s3
        ('publish', 'first', 's3', {'verbosity': 1}),

        # Publish the second app to s3
        ('publish', 'second', 's3', {'verbosity': 1, 'publish_state': 'first'}),
    ]


def test_publish_alternative_channel(publish_command, first_app, second_app):
    "Apps can be published to an alternate channel"
    # Add two apps
    publish_command.apps = {
        'first': first_app,
        'second': second_app,
    }

    # Configure no command line options
    options = publish_command.parse_options(['-c', 'alternative'])

    # Run the publish command
    publish_command(**options)

    # The right sequence of things will be done
    assert publish_command.actions == [
        # Publish the first app to the alternative channel
        ('publish', 'first', 'alternative', {'verbosity': 1}),

        # Publish the second app to the alternative channel
        ('publish', 'second', 'alternative', {'verbosity': 1, 'publish_state': 'first'}),
    ]


def test_non_existent(publish_command, first_app_config, second_app):
    "Requesting a publish of a non-existent app raises an error"
    # Add two apps; use the "config only" version of the first app.
    publish_command.apps = {
        'first': first_app_config,
        'second': second_app,
    }

    # Configure no command line options
    options = publish_command.parse_options([])

    # Invoking the publish command raises an error
    with pytest.raises(BriefcaseCommandError):
        publish_command(**options)

    # The right sequence of things will be done
    assert publish_command.actions == []


def test_unbuilt(publish_command, first_app_unbuilt, second_app):
    "Requesting a publish of an app that has been created, but not built, raises an error"
    # Add two apps; use the "config only" version of the first app.
    publish_command.apps = {
        'first': first_app_unbuilt,
        'second': second_app,
    }

    # Configure no command line options
    options = publish_command.parse_options([])

    # Invoking the publish command raises an error
    with pytest.raises(BriefcaseCommandError):
        publish_command(**options)

    # The right sequence of things will be done
    assert publish_command.actions == []
