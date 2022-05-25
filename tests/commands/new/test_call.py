from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_no_git(new_command):
    """If Git is not installed, an error is raised."""
    # Mock a non-existent git
    integrations = mock.MagicMock()
    integrations.git.verify_git_is_installed.side_effect = BriefcaseCommandError(
        "Briefcase requires git, but it is not installed"
    )
    new_command.integrations = integrations

    # The command will fail tool verification.
    with pytest.raises(
        BriefcaseCommandError, match=r"Briefcase requires git, but it is not installed"
    ):
        new_command()


def test_new_app(new_command):
    """A new application can be created."""

    # Configure no command line options
    options = new_command.parse_options([])

    # Run the run command
    new_command(**options)

    # The right sequence of things will be done
    assert new_command.actions == [
        # Tools are verified
        ("verify",),
        # Run the first app
        ("new", {"template": None}),
    ]
