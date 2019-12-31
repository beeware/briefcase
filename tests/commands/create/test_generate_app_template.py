import subprocess
from datetime import date
from pathlib import Path
from unittest import mock

import pytest
from cookiecutter import exceptions as cookiecutter_exceptions
from git import exc as git_exceptions

from briefcase.commands.base import TemplateUnsupportedVersion
from briefcase.commands.create import InvalidTemplateRepository
from briefcase.exceptions import NetworkFailure


def full_context(extra):
    "The full context associated with myapp"
    context = {
        'app_name': 'my-app',
        'formal_name': 'My App',
        'bundle': 'com.example',
        'version': '1.2.3',
        'description': "This is a simple app",
        'sources': ['src/my_app'],
        'url': None,
        'author': None,
        'author_email': None,
        'requires': None,
        'icon': None,
        'splash': None,
        'document_types': {},

        # Fields generated from other properties
        'module_name': 'my_app',

        # Date-based fields added at time of generation
        'year': date.today().strftime('%Y'),
        'month': date.today().strftime('%B'),

        # Fields added by the output format.
        'output_format': 'dummy',
    }
    context.update(extra)
    return context


def test_default_template(create_command, myapp):
    "Absent of other information, the default template is used"
    # There won't be a cookiecutter cache, so there won't be
    # a cache path (yet).
    create_command.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Generate the template.
    create_command.generate_app_template(myapp)

    # App's template has been set
    assert myapp.template == 'https://github.com/beeware/briefcase-tester-dummy-template.git'

    # Cookiecutter was invoked with the expected template name and context.
    create_command.cookiecutter.assert_called_once_with(
        'https://github.com/beeware/briefcase-tester-dummy-template.git',
        no_input=True,
        checkout=create_command.python_version_tag,
        output_dir=str(create_command.platform_path),
        extra_context=full_context({
            'template': 'https://github.com/beeware/briefcase-tester-dummy-template.git',
        })
    )


def test_platform_exists(create_command, myapp):
    "If the platform directory already exists, it's ok"
    # There won't be a cookiecutter cache, so there won't be
    # a cache path (yet).
    create_command.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Create the platform directory
    create_command.platform_path.mkdir(parents=True)

    # Generate the template.
    create_command.generate_app_template(myapp)

    # App's template has been set
    assert myapp.template == 'https://github.com/beeware/briefcase-tester-dummy-template.git'

    # Cookiecutter was invoked with the expected template name and context.
    create_command.cookiecutter.assert_called_once_with(
        'https://github.com/beeware/briefcase-tester-dummy-template.git',
        no_input=True,
        checkout=create_command.python_version_tag,
        output_dir=str(create_command.platform_path),
        extra_context=full_context({
            'template': 'https://github.com/beeware/briefcase-tester-dummy-template.git',
        })
    )


def test_explicit_repo_template(create_command, myapp):
    "If a template is specified in the app config, it is used"
    myapp.template = 'https://example.com/magic/special-template.git'

    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).
    create_command.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Generate the template.
    create_command.generate_app_template(myapp)

    # App's template hasn't been changed
    assert myapp.template == 'https://example.com/magic/special-template.git'

    # Cookiecutter was invoked with the expected template name and context.
    create_command.cookiecutter.assert_called_once_with(
        'https://example.com/magic/special-template.git',
        no_input=True,
        checkout=create_command.python_version_tag,
        output_dir=str(create_command.platform_path),
        extra_context=full_context({
            'template': 'https://example.com/magic/special-template.git',
        })
    )


def test_explicit_local_template(create_command, myapp):
    "If a local template path is specified in the app config, it is used"
    myapp.template = '/path/to/special-template'

    # Generate the template.
    create_command.generate_app_template(myapp)

    # App's template hasn't been changed
    assert myapp.template == '/path/to/special-template'

    # Cookiecutter was invoked with the expected template name and context.
    create_command.cookiecutter.assert_called_once_with(
        '/path/to/special-template',
        no_input=True,
        checkout=create_command.python_version_tag,
        output_dir=str(create_command.platform_path),
        extra_context=full_context({
            'template': '/path/to/special-template',
        })
    )

    # The template is a local directory, so there won't be any calls on git.
    assert create_command.git.Repo.call_count == 0


def test_offline_repo_template(create_command, myapp):
    "If the user is offline the first time a repo template is requested, an error is raised"
    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).
    create_command.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Calling cookiecutter on a repository while offline causes a CalledProcessError
    create_command.cookiecutter.side_effect = subprocess.CalledProcessError(
        cmd=['git', 'clone', 'https://github.com/beeware/briefcase-tester-dummy-template.git'],
        returncode=128
    )

    # Generating the template under these conditions raises an error
    with pytest.raises(NetworkFailure):
        create_command.generate_app_template(myapp)

    # App's template has been set
    assert myapp.template == 'https://github.com/beeware/briefcase-tester-dummy-template.git'

    # Cookiecutter was invoked with the expected template name and context.
    create_command.cookiecutter.assert_called_once_with(
        'https://github.com/beeware/briefcase-tester-dummy-template.git',
        no_input=True,
        checkout=create_command.python_version_tag,
        output_dir=str(create_command.platform_path),
        extra_context=full_context({
            'template': 'https://github.com/beeware/briefcase-tester-dummy-template.git',
        })
    )


def test_invalid_repo_template(create_command, myapp):
    "If the provided template URL isn't valid, an error is raised"
    myapp.template = 'https://example.com/somewhere/not-a-repo.git'

    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).
    create_command.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Calling cookiecutter on a URL that isn't a valid repository causes an error
    create_command.cookiecutter.side_effect = cookiecutter_exceptions.RepositoryNotFound

    # Generating the template under there conditions raises an error
    with pytest.raises(InvalidTemplateRepository):
        create_command.generate_app_template(myapp)

    # App's template is unchanged
    assert myapp.template == 'https://example.com/somewhere/not-a-repo.git'

    # Cookiecutter was invoked with the expected template name and context.
    create_command.cookiecutter.assert_called_once_with(
        'https://example.com/somewhere/not-a-repo.git',
        no_input=True,
        checkout=create_command.python_version_tag,
        output_dir=str(create_command.platform_path),
        extra_context=full_context({
            'template': 'https://example.com/somewhere/not-a-repo.git',
        })
    )


def test_missing_branch_template(create_command, myapp):
    "If the repo at the provided template URL doesn't have a branch for this Python version, an error is raised"
    myapp.template = 'https://example.com/somewhere/missing-branch.git'

    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).
    create_command.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Calling cookiecutter on a URL that doesn't have the requested branch
    # causes an error
    create_command.cookiecutter.side_effect = cookiecutter_exceptions.RepositoryCloneFailed

    # Generating the template under there conditions raises an error
    with pytest.raises(TemplateUnsupportedVersion):
        create_command.generate_app_template(myapp)

    # App's template is unchanged
    assert myapp.template == 'https://example.com/somewhere/missing-branch.git'

    # Cookiecutter was invoked with the expected template name and context.
    create_command.cookiecutter.assert_called_once_with(
        'https://example.com/somewhere/missing-branch.git',
        no_input=True,
        checkout=create_command.python_version_tag,
        output_dir=str(create_command.platform_path),
        extra_context=full_context({
            'template': 'https://example.com/somewhere/missing-branch.git',
        })
    )


def test_cached_template(create_command, myapp):
    "If a template has already been used, the cached version will be used"
    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()
    mock_remote_head = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote, and it has
    # heads that can be accessed.
    create_command.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_remote.refs.__getitem__.return_value = mock_remote_head

    # Generate the template.
    create_command.generate_app_template(myapp)

    # The origin of the repo was fetched
    mock_repo.remote.assert_called_once_with(name='origin')
    mock_remote.fetch.assert_called_once_with()

    # The remote head was checked out.
    mock_remote_head.checkout.assert_called_once_with()

    # App's config template hasn't changed
    assert myapp.template == 'https://github.com/beeware/briefcase-tester-dummy-template.git'

    # Cookiecutter was invoked with the path to the *cached* template name
    create_command.cookiecutter.assert_called_once_with(
        str(Path.home() / '.cookiecutters' / 'briefcase-tester-dummy-template'),
        no_input=True,
        checkout=create_command.python_version_tag,
        output_dir=str(create_command.platform_path),
        extra_context=full_context({
            'template': 'https://github.com/beeware/briefcase-tester-dummy-template.git',
        })
    )


def test_cached_template_offline(create_command, myapp, capsys):
    "If the user is offline, a cached template won't be updated, but will still work"
    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()
    mock_remote_head = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote, and it has
    # heads that can be accessed. However, calling fetch on the remote
    # will cause a git error (error code 128).
    create_command.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_remote.refs.__getitem__.return_value = mock_remote_head
    mock_remote.fetch.side_effect = git_exceptions.GitCommandError('git', 128)

    # Generate the template.
    create_command.generate_app_template(myapp)

    # An attempt to fetch the repo origin was made
    mock_repo.remote.assert_called_once_with(name='origin')
    mock_remote.fetch.assert_called_once_with()

    # A warning was raised to the user about the fetch problem
    output = capsys.readouterr().out
    assert "WARNING: Unable to update template (is your computer offline?)" in output

    # The remote head was checked out.
    mock_remote_head.checkout.assert_called_once_with()

    # App's config template hasn't changed
    assert myapp.template == 'https://github.com/beeware/briefcase-tester-dummy-template.git'

    # Cookiecutter was invoked with the path to the *cached* template name
    create_command.cookiecutter.assert_called_once_with(
        str(Path.home() / '.cookiecutters' / 'briefcase-tester-dummy-template'),
        no_input=True,
        checkout=create_command.python_version_tag,
        output_dir=str(create_command.platform_path),
        extra_context=full_context({
            'template': 'https://github.com/beeware/briefcase-tester-dummy-template.git',
        })
    )


def test_cached_missing_branch_template(create_command, myapp):
    "If the cached repo doesn't have a branch for this Python version, an error is raised"
    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote. However, it doesn't
    # have a head corresponding to the requested Python version, so it
    # raises an IndexError
    create_command.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_remote.refs.__getitem__.side_effect = IndexError

    # Generating the template under there conditions raises an error
    with pytest.raises(TemplateUnsupportedVersion):
        create_command.generate_app_template(myapp)
