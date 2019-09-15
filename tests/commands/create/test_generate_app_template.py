import subprocess
from datetime import date
from pathlib import Path
from unittest import mock

import pytest
from git import exc as git_exceptions
from cookiecutter import exceptions as cookiecutter_exceptions

from briefcase.commands import CreateCommand
from briefcase.commands.create import (
    NetworkFailure,
    InvalidTemplateRepository,
    TemplateUnsupportedPythonVersion
)
from briefcase.config import Config


class SimpleAppConfig(Config):
    def __init__(self, name, template=None, **kwargs):
        self.name = name
        self.template = template
        super().__init__(**kwargs)


class DummyCreateCommand(CreateCommand):
    def __init__(self):
        super().__init__(platform='tester', output_format='dummy')

        # Mock the two external services
        self.git = mock.MagicMock()
        self.cookiecutter = mock.MagicMock()

    @property
    def template_url(self):
        return 'https://github.com/beeware/briefcase-sample-template.git'

    def binary_path(self, app, base):
        return base / 'tester' / '{app.name}-dummy.bin'.format(app)

    def bundle_path(self, app, base):
        return base / 'tester' / '{app.name}.dummy'.format(app)

    def verify_tools(self):
        pass


@pytest.fixture
def create_command():
    return DummyCreateCommand()


@pytest.fixture
def myapp():
    return SimpleAppConfig(
        name='myapp',
    )


def test_default_template(create_command, myapp, tmp_path):
    "Absent of other information, the default template is used"
    # There won't be a cookiecutter cache, so there won't be
    # a cache path (yet).
    create_command.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Generate the template.
    create_command.generate_app_template(myapp, tmp_path)

    # App's template has been set
    assert myapp.template == 'https://github.com/beeware/briefcase-sample-template.git'

    # Cookiecutter was invoked with the expected template name and context.
    create_command.cookiecutter.assert_called_once_with(
        'https://github.com/beeware/briefcase-sample-template.git',
        no_input=True,
        checkout=create_command.python_version_tag,
        extra_context={
            'name': 'myapp',
            'template': 'https://github.com/beeware/briefcase-sample-template.git',
            'year': date.today().strftime('%Y'),
            'month': date.today().strftime('%B'),
        }
    )


def test_explicit_repo_template(create_command, myapp, tmp_path):
    "If a template is specified in the app config, it is used"
    myapp.template = 'https://github.com/magic/special-template.git'

    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).
    create_command.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Generate the template.
    create_command.generate_app_template(myapp, tmp_path)

    # App's template hasn't been changed
    assert myapp.template == 'https://github.com/magic/special-template.git'

    # Cookiecutter was invoked with the expected template name and context.
    create_command.cookiecutter.assert_called_once_with(
        'https://github.com/magic/special-template.git',
        no_input=True,
        checkout=create_command.python_version_tag,
        extra_context={
            'name': 'myapp',
            'template': 'https://github.com/magic/special-template.git',
            'year': date.today().strftime('%Y'),
            'month': date.today().strftime('%B'),
        }
    )


def test_explicit_local_template(create_command, myapp, tmp_path):
    "If a local template path is specified in the app config, it is used"
    myapp.template = '/path/to/special-template'

    # The template is a local directory, so there won't
    # ever be a cookiecutter cache;
    create_command.git.Repo.side_effect = git_exceptions.InvalidGitRepositoryError

    # Generate the template.
    create_command.generate_app_template(myapp, tmp_path)

    # App's template hasn't been changed
    assert myapp.template == '/path/to/special-template'

    # Cookiecutter was invoked with the expected template name and context.
    create_command.cookiecutter.assert_called_once_with(
        '/path/to/special-template',
        no_input=True,
        checkout=create_command.python_version_tag,
        extra_context={
            'name': 'myapp',
            'template': '/path/to/special-template',
            'year': date.today().strftime('%Y'),
            'month': date.today().strftime('%B'),
        }
    )


def test_offline_repo_template(create_command, myapp, tmp_path):
    "If the user is offline the first time a repo template is requested, an error is raised"
    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).
    create_command.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Calling cookiecutter on a repository while offline causes a CalledProcessError
    create_command.cookiecutter.side_effect = subprocess.CalledProcessError(
        cmd=['git', 'clone', 'https://github.com/beeware/briefcase-sample-template.git'],
        returncode=128
    )

    # Generating the template under there conditions raises an error
    with pytest.raises(NetworkFailure):
        create_command.generate_app_template(myapp, tmp_path)

    # App's template has been set
    assert myapp.template == 'https://github.com/beeware/briefcase-sample-template.git'

    # Cookiecutter was invoked with the expected template name and context.
    create_command.cookiecutter.assert_called_once_with(
        'https://github.com/beeware/briefcase-sample-template.git',
        no_input=True,
        checkout=create_command.python_version_tag,
        extra_context={
            'name': 'myapp',
            'template': 'https://github.com/beeware/briefcase-sample-template.git',
            'year': date.today().strftime('%Y'),
            'month': date.today().strftime('%B'),
        }
    )


def test_invalid_repo_template(create_command, myapp, tmp_path):
    "If the provided template URL isn't valid, an error is raised"
    myapp.template = 'https://github.com/beeware/briefcase-missing-branch-template.git'

    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).
    create_command.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Calling cookiecutter on a URL that isn't a valid repository causes an error
    create_command.cookiecutter.side_effect = cookiecutter_exceptions.RepositoryNotFound

    # Generating the template under there conditions raises an error
    with pytest.raises(InvalidTemplateRepository):
        create_command.generate_app_template(myapp, tmp_path)

    # App's template is unchanged
    assert myapp.template == 'https://github.com/beeware/briefcase-missing-branch-template.git'

    # Cookiecutter was invoked with the expected template name and context.
    create_command.cookiecutter.assert_called_once_with(
        'https://github.com/beeware/briefcase-missing-branch-template.git',
        no_input=True,
        checkout=create_command.python_version_tag,
        extra_context={
            'name': 'myapp',
            'template': 'https://github.com/beeware/briefcase-missing-branch-template.git',
            'year': date.today().strftime('%Y'),
            'month': date.today().strftime('%B'),
        }
    )


def test_missing_branch_template(create_command, myapp, tmp_path):
    "If the repo at the provided template URL doesn't have a branch for this Python version, an error is raised"
    myapp.template = 'https://github.com/not/a-valid-url.git'

    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).
    create_command.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Calling cookiecutter on a URL that doesn't have the requested branch
    # causes an error
    create_command.cookiecutter.side_effect = cookiecutter_exceptions.RepositoryCloneFailed

    # Generating the template under there conditions raises an error
    with pytest.raises(TemplateUnsupportedPythonVersion):
        create_command.generate_app_template(myapp, tmp_path)

    # App's template is unchanged
    assert myapp.template == 'https://github.com/not/a-valid-url.git'

    # Cookiecutter was invoked with the expected template name and context.
    create_command.cookiecutter.assert_called_once_with(
        'https://github.com/not/a-valid-url.git',
        no_input=True,
        checkout=create_command.python_version_tag,
        extra_context={
            'name': 'myapp',
            'template': 'https://github.com/not/a-valid-url.git',
            'year': date.today().strftime('%Y'),
            'month': date.today().strftime('%B'),
        }
    )


def test_cached_template(create_command, myapp, tmp_path):
    "If a template has already been used, the cached version will be used"
    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()
    mock_head = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote, and it has
    # heads that can be accessed.
    create_command.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_repo.heads.__getitem__.return_value = mock_head

    # Generate the template.
    create_command.generate_app_template(myapp, tmp_path)

    # The origin of the repo was fetched
    mock_repo.remote.assert_called_once_with(name='origin')
    mock_remote.fetch.assert_called_once()

    # The head was changed to the python version
    mock_repo.heads.__getitem__.assert_called_once_with(create_command.python_version_tag)
    mock_head.checkout.assert_called_once()

    # App's config template hasn't changed
    assert myapp.template == 'https://github.com/beeware/briefcase-sample-template.git'

    # Cookiecutter was invoked with the path to the *cached* template name
    create_command.cookiecutter.assert_called_once_with(
        Path.home() / '.cookiecutters' / 'briefcase-sample-template',
        no_input=True,
        checkout=create_command.python_version_tag,
        extra_context={
            'name': 'myapp',
            'template': 'https://github.com/beeware/briefcase-sample-template.git',
            'year': date.today().strftime('%Y'),
            'month': date.today().strftime('%B'),
        }
    )


def test_cached_template_offline(create_command, myapp, tmp_path, capsys):
    "If the user is offline, a cached template won't be updated, but will still work"
    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()
    mock_head = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote, and it has
    # heads that can be accessed. However, calling fetch on the remote
    # will cause a git error (error code 128).
    create_command.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_repo.heads.__getitem__.return_value = mock_head
    mock_remote.fetch.side_effect = git_exceptions.GitCommandError('git', 128)

    # Generate the template.
    create_command.generate_app_template(myapp, tmp_path)

    # An attempt to fetch the repo origin was made
    mock_repo.remote.assert_called_once_with(name='origin')
    mock_remote.fetch.assert_called_once()

    # A warning was raised to the user about the fetch problem
    output = capsys.readouterr().out
    assert "WARNING: Unable to update application template (is your computer offline?)" in output

    # The head was changed to the python version
    mock_repo.heads.__getitem__.assert_called_once_with(create_command.python_version_tag)
    mock_head.checkout.assert_called_once()

    # App's config template hasn't changed
    assert myapp.template == 'https://github.com/beeware/briefcase-sample-template.git'

    # Cookiecutter was invoked with the path to the *cached* template name
    create_command.cookiecutter.assert_called_once_with(
        Path.home() / '.cookiecutters' / 'briefcase-sample-template',
        no_input=True,
        checkout=create_command.python_version_tag,
        extra_context={
            'name': 'myapp',
            'template': 'https://github.com/beeware/briefcase-sample-template.git',
            'year': date.today().strftime('%Y'),
            'month': date.today().strftime('%B'),
        }
    )


def test_cached_missing_branch_template(create_command, myapp, tmp_path):
    "If the cached repo doesn't have a branch for this Python version, an error is raised"
    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote. However, it doesn't
    # have a head corresponding to the requested Python version, so it
    # raises an IndexError
    create_command.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_repo.heads.__getitem__.side_effect = IndexError

    # Generating the template under there conditions raises an error
    with pytest.raises(TemplateUnsupportedPythonVersion):
        create_command.generate_app_template(myapp, tmp_path)
