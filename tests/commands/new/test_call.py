import pytest

from briefcase.commands.create import git
from briefcase.exceptions import BriefcaseCommandError


def test_no_git(new_command, monkeypatch):
    """If Git is not installed, an error is raised."""

    def monkeypatch_verify_git(*a, **kw):
        raise BriefcaseCommandError("Briefcase requires git, but it is not installed")

    monkeypatch.setattr(git, "verify_git_is_installed", monkeypatch_verify_git)

    # The command will fail tool verification.
    with pytest.raises(
        BriefcaseCommandError, match=r"Briefcase requires git, but it is not installed"
    ):
        new_command()


def test_parse_config(new_command):
    """Attempting to parse the config is a no-op when invoking new."""
    assert new_command.parse_config("some_file.toml") is None


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
