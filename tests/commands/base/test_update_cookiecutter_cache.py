import re
import shutil
from unittest import mock

import pytest
from git import exc as git_exceptions

from briefcase.exceptions import BriefcaseCommandError, InvalidTemplateBranch

from ...utils import create_file


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


def test_new_repo_template(base_command, mock_git):
    """If a previously unknown URL template is specified it is used."""
    base_command.tools.git = mock_git

    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).

    cached_template = base_command.update_cookiecutter_cache(
        template="https://example.com/magic/special-template.git",
        branch="special",
    )

    # The template that will be used is the original URL
    assert cached_template == base_command.data_path / "templates" / "special-template"

    # A shallow clone is performed.
    base_command.tools.git.Repo.clone_from.assert_called_once_with(
        url="https://example.com/magic/special-template.git",
        to_path=base_command.data_path / "templates" / "special-template",
        filter=["blob:none"],
        no_checkout=True,
    )


def test_new_repo_template_interrupt(base_command, mock_git):
    """If the user raises a keyboard interrupt while cloning, the template is cleaned
    up."""
    base_command.tools.git = mock_git

    # Raise a KeyboardInterrupt during a the clone, having written the git config file.
    def clone_failure(to_path, **kwargs):
        create_file(to_path / ".git" / "config", "git config")
        raise KeyboardInterrupt()

    # Prime the error when the clone is interrupted
    base_command.tools.git.Repo.clone_from.side_effect = clone_failure

    with pytest.raises(KeyboardInterrupt):
        base_command.update_cookiecutter_cache(
            template="https://example.com/magic/special-template.git",
            branch="special",
        )

    # The template directory should be cleaned up
    assert not (base_command.data_path / "templates" / "special-template").exists()


def test_new_repo_template_mkdir_interrupt(base_command, mock_git):
    """A really early interrupt will occur before the template dir is created."""
    base_command.tools.git = mock_git

    # We don't have a convenient point to insert a KeyboardInterrupt *before* creating the
    # directory, so we fake the effect - make the side effect of the clone deletion of
    # the entire folder; then raise the KeyboardInterrupt.
    def clone_failure(to_path, **kwargs):
        shutil.rmtree(to_path)
        raise KeyboardInterrupt()

    # Prime the error when the clone is interrupted
    base_command.tools.git.Repo.clone_from.side_effect = clone_failure

    with pytest.raises(KeyboardInterrupt):
        base_command.update_cookiecutter_cache(
            template="https://example.com/magic/special-template.git",
            branch="special",
        )

    # The template directory shouldn't exist
    assert not (base_command.data_path / "templates" / "special-template").exists()


def test_new_repo_invalid_template_url(base_command, mock_git):
    """If a previously unknown URL template is specified it is used."""
    base_command.tools.git = mock_git

    # Prime the error when the repo doesn't exist
    base_command.tools.git.Repo.clone_from.side_effect = git_exceptions.GitCommandError(
        "git", 128
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Unable to clone repository 'https://example.com/magic/special-template.git'"
        ),
    ):
        base_command.update_cookiecutter_cache(
            template="https://example.com/magic/special-template.git",
            branch="special",
        )

    # The cookiecutter cache location will be interrogated.
    base_command.tools.git.Repo.clone_from.assert_called_once_with(
        url="https://example.com/magic/special-template.git",
        to_path=base_command.data_path / "templates" / "special-template",
        filter=["blob:none"],
        no_checkout=True,
    )

    # The template directory should be cleaned up
    assert not (base_command.data_path / "templates" / "special-template").exists()


@pytest.mark.parametrize(
    ("stderr_string", "error_message"),
    (
        pytest.param(
            "\n    stderr: '\nfatal: could not clone repository 'https://example.com' \n'",
            "Could not clone repository 'https://example.com'.",
            id="tailing-whitespace-no-caps-no-period",
        ),
        pytest.param(
            (
                "\n    stderr: '\nfatal: Could not read from remote repository.\n\n"
                "Please make sure you have the correct access rights\nand the repository exists. \n'"
            ),
            (
                "Could not read from remote repository.\n\nPlease make sure "
                "you have the correct access rights\nand the repository exists."
            ),
            id="tailing-whitespace-has-caps-has-period",
        ),
        pytest.param(
            (
                "\n    stderr: '\nfatal: unable to access 'https://example.com/': "
                "OpenSSL/3.2.2: error:0A000438:SSL routines::tlsv1 alert internal error'"
            ),
            (
                "Unable to access 'https://example.com/': OpenSSL/3.2.2: "
                "error:0A000438:SSL routines::tlsv1 alert internal error."
            ),
            id="no-tailing-whitespace-no-caps-no-period",
        ),
        pytest.param(
            "\n stderr: 'Mysterious git clone edge case with no fatal error.",
            "This may be because your computer is offline",
            id="fallback-hint",
        ),
    ),
)
def test_repo_clone_error(stderr_string, error_message, base_command, mock_git):
    """If git emits error information when cloning, Briefcase provides that to the user.
    If git does not emit a 'fatal' error, then fallback to a generic hint."""
    base_command.tools.git = mock_git

    base_command.tools.git.Repo.clone_from.side_effect = git_exceptions.GitCommandError(
        "git", 128, stderr_string
    )

    repository = "https://example.com"

    with pytest.raises(
        BriefcaseCommandError,
        # The error message should not retain the "fatal:" prefix; it isn't useful information to the user.
        match=f"Unable to clone repository '{re.escape(repository)}'.\n\n?(?<!fatal: ){re.escape(error_message)}",
    ):
        base_command.update_cookiecutter_cache(
            template=repository,
            branch="briefcase-template",
        )


def test_existing_repo_template(base_command, mock_git):
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
    mock_remote.url = "https://example.com/magic/special-template.git"

    cached_path = base_command.template_cache_path(
        "https://example.com/magic/special-template.git"
    )
    cached_path.mkdir(parents=True)

    # Update the cache
    cached_template = base_command.update_cookiecutter_cache(
        template="https://example.com/magic/special-template.git",
        branch="special",
    )

    # The cookiecutter cache location will be interrogated.
    base_command.tools.git.Repo.assert_called_once_with(cached_path)

    # The origin of the repo was updated and fetched
    mock_repo.remote.assert_called_once_with(name="origin")
    mock_remote.set_url.assert_called_once_with(
        new_url="https://example.com/magic/special-template.git",
    )
    mock_remote.fetch.assert_called_once_with()

    # The right branch was accessed
    mock_remote.refs.__getitem__.assert_called_once_with("special")

    # The remote head was checked out.
    mock_remote_head.checkout.assert_called_once_with()

    # The template that will be used is the original URL
    assert cached_template == cached_path


def test_existing_repo_template_corrupted(base_command, mock_git):
    """If a previously cached URL template is in a corrupted state, it is deleted and
    re-cloned."""
    # Git returns an exception wrapping the given URL.
    base_command.tools.git = mock_git
    base_command.tools.git.Repo.side_effect = [
        git_exceptions.GitCommandError("git", 128),
        None,
    ]

    cached_path = base_command.template_cache_path(
        "https://example.com/magic/special-template.git"
    )

    # Create a bad cached template
    create_file(cached_path / "bad-template", "Bad template")

    cached_template = base_command.update_cookiecutter_cache(
        template="https://example.com/magic/special-template.git",
        branch="special",
    )

    # The template that will be used is the original URL
    assert cached_template == base_command.data_path / "templates" / "special-template"

    # An attempt was made to wrap the old repo
    base_command.tools.git.Repo.assert_called_once_with(cached_path)

    # A shallow clone is performed.
    base_command.tools.git.Repo.clone_from.assert_called_once_with(
        url="https://example.com/magic/special-template.git",
        to_path=base_command.data_path / "templates" / "special-template",
        filter=["blob:none"],
        no_checkout=True,
    )

    # The old template content has been deleted
    assert not (cached_path / "bad-template").exists()


def test_existing_repo_template_with_different_url(base_command, mock_git):
    """If a previously known URL template is specified but uses a different remote URL,
    the repo's origin URL is updated and is used."""
    base_command.tools.git = mock_git

    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()
    mock_remote_head = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote, and it has
    # heads that can be accessed.
    base_command.tools.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_remote.refs.__getitem__.return_value = mock_remote_head
    mock_remote.url = "https://example.com/existing/special-template.git"

    cached_path = base_command.template_cache_path(
        "https://example.com/magic/special-template.git"
    )
    cached_path.mkdir(parents=True)

    # Update the cache
    cached_template = base_command.update_cookiecutter_cache(
        template="https://example.com/magic/special-template.git",
        branch="special",
    )

    # The cookiecutter cache location will be interrogated.
    base_command.tools.git.Repo.assert_called_once_with(cached_path)

    # The origin of the repo was updated and fetched
    mock_repo.remote.assert_called_once_with(name="origin")
    mock_remote.set_url.assert_called_once_with(
        new_url="https://example.com/magic/special-template.git",
    )
    mock_remote.fetch.assert_called_once_with()

    # The right branch was accessed
    mock_remote.refs.__getitem__.assert_called_once_with("special")

    # The remote head was checked out.
    mock_remote_head.checkout.assert_called_once_with()

    # The template that will be used is the original URL
    assert cached_template == cached_path


def test_offline_repo_template(base_command, mock_git, capsys):
    """If the user is offline the when a repo template is requested, but the branch
    exists, the command continues with a warning."""
    base_command.tools.git = mock_git

    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()
    mock_remote_head = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote, and it has
    # heads that can be accessed. However, calling fetch on the remote
    # will cause a git error (error code 128).
    base_command.tools.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_remote.url = "https://example.com/magic/special-template.git"
    mock_remote.refs.__getitem__.return_value = mock_remote_head
    mock_remote.fetch.side_effect = git_exceptions.GitCommandError("git", 128)

    cached_path = base_command.template_cache_path(
        "https://example.com/magic/special-template.git"
    )
    cached_path.mkdir(parents=True)

    # Update the cache
    cached_template = base_command.update_cookiecutter_cache(
        template="https://example.com/magic/special-template.git", branch="special"
    )

    # The cookiecutter cache location will be interrogated.
    base_command.tools.git.Repo.assert_called_once_with(cached_path)

    # The origin of the repo was updated and fetched
    mock_repo.remote.assert_called_once_with(name="origin")
    mock_remote.set_url.assert_called_once_with(
        new_url="https://example.com/magic/special-template.git",
    )
    mock_remote.fetch.assert_called_once_with()

    # The right branch was accessed
    mock_remote.refs.__getitem__.assert_called_once_with("special")

    # The remote head was checked out.
    mock_remote_head.checkout.assert_called_once_with()

    # The template that will be used is the original URL
    assert cached_template == cached_path

    # A warning was raised about the template possibly being stale.
    assert "WARNING: Unable to update template" in capsys.readouterr().out


def test_cached_missing_branch_template(base_command, mock_git):
    """If the cached repo doesn't have the requested branch, an error is raised."""
    base_command.tools.git = mock_git

    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote. However, it doesn't
    # have a head corresponding to the requested Python version, so it
    # raises an IndexError
    base_command.tools.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_remote.url = "https://example.com/magic/special-template.git"
    mock_remote.refs.__getitem__.side_effect = IndexError

    cached_path = base_command.template_cache_path(
        "https://example.com/magic/special-template.git"
    )
    cached_path.mkdir(parents=True)

    # Generating the template under there conditions raises an error
    with pytest.raises(InvalidTemplateBranch):
        base_command.update_cookiecutter_cache(
            template="https://example.com/magic/special-template.git",
            branch="invalid",
        )

    # The cookiecutter cache location will be interrogated.
    base_command.tools.git.Repo.assert_called_once_with(cached_path)

    # The origin of the repo was updated and fetched
    mock_repo.remote.assert_called_once_with(name="origin")
    mock_remote.set_url.assert_called_once_with(
        new_url="https://example.com/magic/special-template.git",
    )
    mock_remote.fetch.assert_called_once_with()

    # An attempt to access the branch was made
    mock_remote.refs.__getitem__.assert_called_once_with("invalid")


def test_git_repo_with_missing_origin_remote(base_command, mock_git):
    """If the local git repo doesn't have an origin remote, a ValueError is raised."""
    base_command.tools.git = mock_git

    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote, and it has heads that can be
    # accessed. However, getting the remote will fail if git clone is not complete.
    base_command.tools.git.Repo.return_value = mock_repo
    mock_repo.remote.side_effect = ValueError("Remote named origin did not exist")

    cached_path = base_command.template_cache_path(
        "https://example.com/magic/special-template.git"
    )
    cached_path.mkdir(parents=True)

    # Update the cache
    with pytest.raises(
        BriefcaseCommandError,
        match="Unable to check out template branch.",
    ):
        base_command.update_cookiecutter_cache(
            template="https://example.com/magic/special-template.git", branch="special"
        )

    # The cookiecutter cache location will be interrogated.
    base_command.tools.git.Repo.assert_called_once_with(cached_path)

    # The origin of the repo was not updated or fetched
    mock_repo.remote.assert_called_once_with(name="origin")
    mock_remote.set_url.assert_not_called()
    mock_remote.fetch.assert_not_called()
