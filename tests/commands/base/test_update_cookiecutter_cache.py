from unittest import mock

import pytest
from git import exc as git_exceptions

from briefcase.commands.base import TemplateUnsupportedVersion, cookiecutter_cache_path


def test_non_url(base_command, mock_git):
    """If the provided template isn't a URL, don't try to update."""
    base_command.tools.git = mock_git

    cached_template = base_command.update_cookiecutter_cache(
        template="/path/to/template",
        branch="special",
    )

    assert cached_template == "/path/to/template"
    # No git actions are performed
    assert base_command.tools.git.Repo.call_count == 0


def test_explicit_new_repo_template(base_command, mock_git):
    """If a previously unknown URL template is specified it is used."""
    base_command.tools.git = mock_git

    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).
    base_command.tools.git.Repo.side_effect = git_exceptions.NoSuchPathError

    cached_path = cookiecutter_cache_path(
        "https://example.com/magic/special-template.git"
    )

    # Update the cache
    cached_template = base_command.update_cookiecutter_cache(
        template="https://example.com/magic/special-template.git",
        branch="special",
    )

    # The template that will be used is the original URL
    assert cached_template == "https://example.com/magic/special-template.git"

    # The cookiecutter cache location will be interrogated.
    base_command.tools.git.Repo.assert_called_once_with(cached_path)


def test_explicit_invalid_repo_template(base_command, mock_git):
    """If a previously known URL template is cached, but isn't a git
    repository, it is used as-is."""
    base_command.tools.git = mock_git

    # Return an error from updating the template
    base_command.tools.git.Repo.side_effect = git_exceptions.InvalidGitRepositoryError

    cached_path = cookiecutter_cache_path(
        "https://example.com/magic/special-template.git"
    )

    # Update the cache
    cached_template = base_command.update_cookiecutter_cache(
        template="https://example.com/magic/special-template.git",
        branch="special",
    )

    # The template that will be used is the original URL
    assert cached_template == "https://example.com/magic/special-template.git"

    # The cookiecutter cache location will be interrogated.
    base_command.tools.git.Repo.assert_called_once_with(cached_path)


def test_explicit_cached_repo_template(base_command, mock_git):
    """If a previously known URL template is specified it is used."""
    base_command.tools.git = mock_git

    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()
    mock_remote_head = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote, and it has
    # heads that can be accessed.
    base_command.tools.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_remote.refs.__getitem__.return_value = mock_remote_head

    cached_path = cookiecutter_cache_path(
        "https://example.com/magic/special-template.git"
    )

    # Update the cache
    cached_template = base_command.update_cookiecutter_cache(
        template="https://example.com/magic/special-template.git",
        branch="special",
    )

    # The cookiecutter cache location will be interrogated.
    base_command.tools.git.Repo.assert_called_once_with(cached_path)

    # The origin of the repo was fetched
    mock_repo.remote.assert_called_once_with(name="origin")
    mock_remote.fetch.assert_called_once_with()

    # The right branch was accessed
    mock_remote.refs.__getitem__.assert_called_once_with("special")

    # The remote head was checked out.
    mock_remote_head.checkout.assert_called_once_with()

    # The template that will be used is the original URL
    assert cached_template == cached_path


def test_offline_repo_template(base_command, mock_git):
    """If the user is offline the first time a repo template is requested, an
    error is raised."""
    base_command.tools.git = mock_git

    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()
    mock_remote_head = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote, and it has
    # heads that can be accessed. However, calling fetch on the remote
    # will cause a git error (error code 128).
    base_command.tools.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_remote.refs.__getitem__.return_value = mock_remote_head
    mock_remote.fetch.side_effect = git_exceptions.GitCommandError("git", 128)

    cached_path = cookiecutter_cache_path(
        "https://example.com/magic/special-template.git"
    )

    # Update the cache
    cached_template = base_command.update_cookiecutter_cache(
        template="https://example.com/magic/special-template.git", branch="special"
    )

    # The cookiecutter cache location will be interrogated.
    base_command.tools.git.Repo.assert_called_once_with(cached_path)

    # The origin of the repo was fetched
    mock_repo.remote.assert_called_once_with(name="origin")
    mock_remote.fetch.assert_called_once_with()

    # The right branch was accessed
    mock_remote.refs.__getitem__.assert_called_once_with("special")

    # The remote head was checked out.
    mock_remote_head.checkout.assert_called_once_with()

    # The template that will be used is the original URL
    assert cached_template == cached_path


def test_cached_missing_branch_template(base_command, mock_git):
    """If the cached repo doesn't have the requested branch, an error is
    raised."""
    base_command.tools.git = mock_git

    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote. However, it doesn't
    # have a head corresponding to the requested Python version, so it
    # raises an IndexError
    base_command.tools.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_remote.refs.__getitem__.side_effect = IndexError

    cached_path = cookiecutter_cache_path(
        "https://example.com/magic/special-template.git"
    )

    # Generating the template under there conditions raises an error
    with pytest.raises(TemplateUnsupportedVersion):
        base_command.update_cookiecutter_cache(
            template="https://example.com/magic/special-template.git",
            branch="invalid",
        )

    # The cookiecutter cache location will be interrogated.
    base_command.tools.git.Repo.assert_called_once_with(cached_path)

    # The origin of the repo was fetched
    mock_repo.remote.assert_called_once_with(name="origin")
    mock_remote.fetch.assert_called_once_with()

    # An attempt to access the branch was made
    mock_remote.refs.__getitem__.assert_called_once_with("invalid")
