from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_git(tracking_create_command):
    "If Git is not installed, an error is raised"
    # Mock a non-existent git
    integrations = mock.MagicMock()
    integrations.git.verify_git_is_installed.side_effect = BriefcaseCommandError(
        "Briefcase requires git, but it is not installed"
    )
    tracking_create_command.integrations = integrations

    # The command will fail tool verification.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Briefcase requires git, but it is not installed"
    ):
        tracking_create_command()


def test_create(tracking_create_command):
    "The create command can be called"
    tracking_create_command()

    # The right sequence of things will be done
    first_app = tracking_create_command.apps['first']
    second_app = tracking_create_command.apps['second']
    assert tracking_create_command.actions == [
        ('verify'),

        # Create the first app
        ('check_bundle_path_existence', first_app, None),
        ('generate', first_app),
        ('support', first_app),
        ('dependencies', first_app),
        ('code', first_app),
        ('resources', first_app),

        # Create the second app
        ('check_bundle_path_existence', second_app, None),
        ('generate', second_app),
        ('support', second_app),
        ('dependencies', second_app),
        ('code', second_app),
        ('resources', second_app),
    ]

    # New app content has been created
    assert (tracking_create_command.platform_path / 'first.bundle' / 'new').exists()
    assert (tracking_create_command.platform_path / 'second.bundle' / 'new').exists()


def test_create_single(tracking_create_command):
    "The create command can be called to create a single app from the config"
    first_app = tracking_create_command.apps['first']
    tracking_create_command(app=first_app)

    # The right sequence of things will be done
    assert tracking_create_command.actions == [
        ('verify'),

        # Create the first app
        ('check_bundle_path_existence', first_app, None),
        ('generate', first_app),
        ('support', first_app),
        ('dependencies', first_app),
        ('code', first_app),
        ('resources', first_app),
    ]

    # New app content has been created
    assert (tracking_create_command.platform_path / 'first.bundle' / 'new').exists()
    assert not (tracking_create_command.platform_path / 'second.bundle' / 'new').exists()


def test_create_single_with_override_true(tracking_create_command):
    """The create command can be called with "override" flag that indicates that
     output directory will be override if it already exists
     """
    first_app = tracking_create_command.apps['first']
    tracking_create_command(app=first_app, override=True)

    # The right sequence of things will be done
    assert tracking_create_command.actions == [
        ('verify'),

        # Create the first app
        ('check_bundle_path_existence', first_app, True),
        ('generate', first_app),
        ('support', first_app),
        ('dependencies', first_app),
        ('code', first_app),
        ('resources', first_app),
    ]

    # New app content has been created
    assert (tracking_create_command.platform_path / 'first.bundle' / 'new').exists()
    assert not (tracking_create_command.platform_path / 'second.bundle' / 'new').exists()


def test_create_single_with_override_false(tracking_create_command):
    """The create command can be called with "no-override" flag that indicates that
     command should be aborted output directory already exists
     """
    first_app = tracking_create_command.apps['first']
    tracking_create_command(app=first_app, override=False)

    # The right sequence of things will be done
    assert tracking_create_command.actions == [
        ('verify'),

        # Create the first app
        ('check_bundle_path_existence', first_app, False),
        ('generate', first_app),
        ('support', first_app),
        ('dependencies', first_app),
        ('code', first_app),
        ('resources', first_app),
    ]

    # New app content has been created
    assert (tracking_create_command.platform_path / 'first.bundle' / 'new').exists()
    assert not (tracking_create_command.platform_path / 'second.bundle' / 'new').exists()
