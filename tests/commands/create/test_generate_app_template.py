import os
import platform
import subprocess
from datetime import date
from pathlib import Path
from unittest import mock

import pytest
from cookiecutter import exceptions as cookiecutter_exceptions
from git import exc as git_exceptions

import briefcase
from briefcase.exceptions import (
    InvalidTemplateRepository,
    NetworkFailure,
    TemplateUnsupportedVersion,
)


@pytest.fixture
def full_context():
    return {
        "format": "dummy",
        "app_name": "my-app",
        "formal_name": "My App",
        "bundle": "com.example",
        "bundle_identifier": "com.example.my-app",
        "version": "1.2.3",
        "description": "This is a simple app",
        "long_description": None,
        "sources": ["src/my_app"],
        "test_sources": None,
        "test_requires": None,
        "url": "https://example.com",
        "author": "First Last",
        "author_email": "first@example.com",
        "requires": None,
        "icon": None,
        "splash": None,
        "supported": True,
        "permissions": {},
        "custom_permissions": {},
        "requests": {},
        "document_types": {},
        # Properties of the generating environment
        "python_version": platform.python_version(),
        "host_arch": "gothic",
        "briefcase_version": briefcase.__version__,
        # Fields generated from other properties
        "module_name": "my_app",
        "class_name": "MyApp",
        "package_name": "com.example",
        # Date-based fields added at time of generation
        "year": date.today().strftime("%Y"),
        "month": date.today().strftime("%B"),
        # Fields added by the output format.
        "output_format": "dummy",
        # These tests don't do a full finalization, so the context will still be
        # marked as draft.
        "__draft__": True,
    }


@pytest.mark.parametrize(
    "briefcase_version, expected_branch",
    [
        ("37.42.1", "v37.42.1"),
        ("37.42.2.dev0+gad61a29.d20220919", "v37.42.2"),
        ("37.42.3.dev73+gad61a29.d20220919", "v37.42.3"),
        ("37.42.4a1", "v37.42.4"),
        ("37.42.5b2", "v37.42.5"),
        ("37.42.6rc3", "v37.42.6"),
        ("37.42.7.post1", "v37.42.7"),
    ],
)
def test_default_template(
    monkeypatch,
    create_command,
    myapp,
    full_context,
    briefcase_version,
    expected_branch,
    tmp_path,
):
    """Absent of other information, the briefcase version (without suffixes) is used as
    the template branch."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", briefcase_version)
    full_context["briefcase_version"] = briefcase_version

    # There won't be a cookiecutter cache, so there won't be
    # a cache path (yet).
    create_command.tools.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Generate the template.
    create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    create_command.tools.cookiecutter.assert_called_once_with(
        "https://github.com/beeware/briefcase-Tester-Dummy-template.git",
        no_input=True,
        checkout=expected_branch,
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
    )


@pytest.mark.parametrize(
    "briefcase_version",
    ("37.42.7.dev0+gad61a29.d20220919", "37.42.7.dev73+gad61a29.d20220919"),
)
def test_default_template_dev(
    monkeypatch,
    create_command,
    myapp,
    full_context,
    briefcase_version,
    tmp_path,
):
    """In a dev version, template will fall back to the 'main' branch if a versioned
    template doesn't exist."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", briefcase_version)
    full_context["briefcase_version"] = briefcase_version

    # There won't be a cookiecutter cache, so there won't be
    # a cache path (yet).
    create_command.tools.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # There will be two calls to cookiecutter; one on the versioned branch,
    # and one on the `main` branch. The first call will fail because the
    # template doesn't exist yet; the second will succeed.
    create_command.tools.cookiecutter.side_effect = [
        cookiecutter_exceptions.RepositoryCloneFailed,
        None,
    ]

    # Generate the template.
    create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    assert create_command.tools.cookiecutter.mock_calls == [
        mock.call(
            "https://github.com/beeware/briefcase-Tester-Dummy-template.git",
            no_input=True,
            checkout="v37.42.7",
            output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
            extra_context=full_context,
        ),
        mock.call(
            "https://github.com/beeware/briefcase-Tester-Dummy-template.git",
            no_input=True,
            checkout="main",
            output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
            extra_context=full_context,
        ),
    ]


@pytest.mark.parametrize(
    "briefcase_version",
    ("37.42.7.dev0+gad61a29.d20220919", "37.42.7.dev73+gad61a29.d20220919"),
)
def test_default_template_dev_explicit_branch(
    monkeypatch,
    create_command,
    myapp,
    full_context,
    briefcase_version,
    tmp_path,
):
    """In a dev version, if an explicit branch is provided, it is used."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", briefcase_version)
    full_context["briefcase_version"] = briefcase_version

    # Set an explicit branch
    branch = "some_branch"
    myapp.template_branch = branch

    # There won't be a cookiecutter cache, so there won't be
    # a cache path (yet).
    create_command.tools.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Generate the template.
    create_command.generate_app_template(myapp)

    # Cookiecutter was invoked (once) with the expected template name and context.
    assert create_command.tools.cookiecutter.mock_calls == [
        mock.call(
            "https://github.com/beeware/briefcase-Tester-Dummy-template.git",
            no_input=True,
            checkout=branch,
            output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
            extra_context=full_context,
        ),
    ]


@pytest.mark.parametrize(
    "briefcase_version",
    ("37.42.7.dev0+gad61a29.d20220919", "37.42.7.dev73+gad61a29.d20220919"),
)
def test_default_template_dev_explicit_invalid_branch(
    monkeypatch,
    create_command,
    myapp,
    full_context,
    briefcase_version,
    tmp_path,
):
    """In a dev version, if an explicit (but invalid) branch is provided, the fallback
    to the 'main' branch will not occur."""
    # Set the Briefcase version to a dev version
    monkeypatch.setattr(briefcase, "__version__", briefcase_version)
    full_context["briefcase_version"] = briefcase_version

    # Set an explicit branch
    branch = "some_branch"
    myapp.template_branch = branch

    # There won't be a cookiecutter cache, so there won't be
    # a cache path (yet).
    create_command.tools.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # There will be only 1 call to cookiecutter; the one on the versioned branch.
    create_command.tools.cookiecutter.side_effect = (
        cookiecutter_exceptions.RepositoryCloneFailed
    )

    # Generate the template.
    with pytest.raises(TemplateUnsupportedVersion):
        create_command.generate_app_template(myapp)

    # Cookiecutter was invoked (once) with the expected template name and context.
    assert create_command.tools.cookiecutter.mock_calls == [
        mock.call(
            "https://github.com/beeware/briefcase-Tester-Dummy-template.git",
            no_input=True,
            checkout=branch,
            output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
            extra_context=full_context,
        ),
    ]


def test_explicit_branch(monkeypatch, create_command, myapp, full_context, tmp_path):
    """User can choose which branch to take the template from."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"

    # Set an explicit branch
    branch = "some_branch"
    myapp.template_branch = branch

    # There won't be a cookiecutter cache, so there won't be
    # a cache path (yet).
    create_command.tools.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Generate the template.
    create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    create_command.tools.cookiecutter.assert_called_once_with(
        "https://github.com/beeware/briefcase-Tester-Dummy-template.git",
        no_input=True,
        checkout=branch,
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
    )


def test_platform_exists(monkeypatch, create_command, myapp, full_context, tmp_path):
    """If the platform directory already exists, it's ok."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"

    # There won't be a cookiecutter cache, so there won't be
    # a cache path (yet).
    create_command.tools.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Create the build directory
    create_command.build_path(myapp).mkdir(parents=True)

    # Generate the template.
    create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    create_command.tools.cookiecutter.assert_called_once_with(
        "https://github.com/beeware/briefcase-Tester-Dummy-template.git",
        no_input=True,
        checkout="v37.42.7",
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
    )


def test_explicit_repo_template(
    monkeypatch, create_command, myapp, full_context, tmp_path
):
    """If a template is specified in the app config, it is used."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"

    myapp.template = "https://example.com/magic/special-template.git"

    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).
    create_command.tools.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Generate the template.
    create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    create_command.tools.cookiecutter.assert_called_once_with(
        "https://example.com/magic/special-template.git",
        no_input=True,
        checkout="v37.42.7",
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
    )


def test_explicit_repo_template_and_branch(
    monkeypatch,
    create_command,
    myapp,
    full_context,
    tmp_path,
):
    """If a template and branch is specified in the app config, it is used."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"

    # Set an explicit template and branch
    myapp.template = "https://example.com/magic/special-template.git"
    branch = "some_branch"
    myapp.template_branch = branch

    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).
    create_command.tools.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Generate the template.
    create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    create_command.tools.cookiecutter.assert_called_once_with(
        "https://example.com/magic/special-template.git",
        no_input=True,
        checkout=branch,
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
    )


def test_explicit_local_template(
    monkeypatch, create_command, myapp, full_context, tmp_path
):
    """If a local template path is specified in the app config, it is used."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"

    myapp.template = "/path/to/special-template"

    # Generate the template.
    create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    create_command.tools.cookiecutter.assert_called_once_with(
        "/path/to/special-template",
        no_input=True,
        checkout="v37.42.7",
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
    )

    # The template is a local directory, so there won't be any calls on git.
    assert create_command.tools.git.Repo.call_count == 0


def test_explicit_local_template_and_branch(
    monkeypatch,
    create_command,
    myapp,
    full_context,
    tmp_path,
):
    """If a local template path and branch is specified in the app config, it is
    used."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"

    myapp.template = "/path/to/special-template"
    branch = "some_branch"
    myapp.template_branch = branch

    # Generate the template.
    create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    create_command.tools.cookiecutter.assert_called_once_with(
        "/path/to/special-template",
        no_input=True,
        checkout=branch,
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
    )

    # The template is a local directory, so there won't be any calls on git.
    assert create_command.tools.git.Repo.call_count == 0


def test_offline_repo_template(
    monkeypatch, create_command, myapp, full_context, tmp_path
):
    """If the user is offline the first time a repo template is requested, an error is
    raised."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"

    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).
    create_command.tools.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Calling cookiecutter on a repository while offline causes a CalledProcessError
    create_command.tools.cookiecutter.side_effect = subprocess.CalledProcessError(
        cmd=[
            "git",
            "clone",
            "https://github.com/beeware/briefcase-Tester-Dummy-template.git",
        ],
        returncode=128,
    )

    # Generating the template under these conditions raises an error
    with pytest.raises(NetworkFailure):
        create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    create_command.tools.cookiecutter.assert_called_once_with(
        "https://github.com/beeware/briefcase-Tester-Dummy-template.git",
        no_input=True,
        checkout="v37.42.7",
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
    )


def test_invalid_repo_template(
    monkeypatch, create_command, myapp, full_context, tmp_path
):
    """If the provided template URL isn't valid, an error is raised."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"

    myapp.template = "https://example.com/somewhere/not-a-repo.git"

    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).
    create_command.tools.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Calling cookiecutter on a URL that isn't a valid repository causes an error
    create_command.tools.cookiecutter.side_effect = (
        cookiecutter_exceptions.RepositoryNotFound
    )

    # Generating the template under there conditions raises an error
    with pytest.raises(InvalidTemplateRepository):
        create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    create_command.tools.cookiecutter.assert_called_once_with(
        "https://example.com/somewhere/not-a-repo.git",
        no_input=True,
        checkout="v37.42.7",
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
    )


def test_missing_branch_template(
    monkeypatch, create_command, myapp, full_context, tmp_path
):
    """If the repo at the provided template URL doesn't have a branch for this Briefcase
    version, an error is raised."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"

    myapp.template = "https://example.com/somewhere/missing-branch.git"

    # There won't be a cookiecutter cache, so there won't be
    # a repo path (yet).
    create_command.tools.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Calling cookiecutter on a URL that doesn't have the requested branch
    # causes an error
    create_command.tools.cookiecutter.side_effect = (
        cookiecutter_exceptions.RepositoryCloneFailed
    )

    # Generating the template under there conditions raises an error
    with pytest.raises(TemplateUnsupportedVersion):
        create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    create_command.tools.cookiecutter.assert_called_once_with(
        "https://example.com/somewhere/missing-branch.git",
        no_input=True,
        checkout="v37.42.7",
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
    )


def test_cached_template(monkeypatch, create_command, myapp, full_context, tmp_path):
    """If a template has already been used, the cached version will be used."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"

    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()
    mock_remote_head = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote, and it has
    # heads that can be accessed.
    create_command.tools.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_remote.refs.__getitem__.return_value = mock_remote_head

    # Generate the template.
    create_command.generate_app_template(myapp)

    # The origin of the repo was fetched
    mock_repo.remote.assert_called_once_with(name="origin")
    mock_remote.fetch.assert_called_once_with()

    # The remote head was checked out.
    mock_remote_head.checkout.assert_called_once_with()

    # Cookiecutter was invoked with the path to the *cached* template name
    create_command.tools.cookiecutter.assert_called_once_with(
        os.fsdecode(Path.home() / ".cookiecutters/briefcase-Tester-Dummy-template"),
        no_input=True,
        checkout="v37.42.7",
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
    )


def test_cached_template_offline(
    monkeypatch,
    create_command,
    myapp,
    full_context,
    capsys,
    tmp_path,
):
    """If the user is offline, a cached template won't be updated, but will still
    work."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"

    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()
    mock_remote_head = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote, and it has
    # heads that can be accessed. However, calling fetch on the remote
    # will cause a git error (error code 128).
    create_command.tools.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_remote.refs.__getitem__.return_value = mock_remote_head
    mock_remote.fetch.side_effect = git_exceptions.GitCommandError("git", 128)

    # Generate the template.
    create_command.generate_app_template(myapp)

    # An attempt to fetch the repo origin was made
    mock_repo.remote.assert_called_once_with(name="origin")
    mock_remote.fetch.assert_called_once_with()

    # A warning was raised to the user about the fetch problem
    output = capsys.readouterr().out
    assert "** WARNING: Unable to update template" in output

    # The remote head was checked out.
    mock_remote_head.checkout.assert_called_once_with()

    # Cookiecutter was invoked with the path to the *cached* template name
    create_command.tools.cookiecutter.assert_called_once_with(
        os.fsdecode(Path.home() / ".cookiecutters/briefcase-Tester-Dummy-template"),
        no_input=True,
        checkout="v37.42.7",
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
    )


def test_cached_missing_branch_template(monkeypatch, create_command, myapp):
    """If the cached repo doesn't have a branch for this Briefcase version, an error is
    raised."""
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")

    mock_repo = mock.MagicMock()
    mock_remote = mock.MagicMock()

    # Git returns a Repo, that repo can return a remote. However, it doesn't
    # have a head corresponding to the requested Python version, so it
    # raises an IndexError
    create_command.tools.git.Repo.return_value = mock_repo
    mock_repo.remote.return_value = mock_remote
    mock_remote.refs.__getitem__.side_effect = IndexError

    # Generating the template under there conditions raises an error
    with pytest.raises(TemplateUnsupportedVersion):
        create_command.generate_app_template(myapp)


def test_x_permissions(
    monkeypatch,
    create_command,
    myapp,
    full_context,
    tmp_path,
):
    # Set the Briefcase version
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    full_context["briefcase_version"] = "37.42.7"

    # Define some permissions and requests. The original "permission" and "request"
    # definitions will be hidden from the final template context.

    myapp.permission = {
        # Cross-platform permissions
        "camera": "I need to see you",
        "microphone": "I need to hear you",
        "coarse_location": "I need to know approximately where you are",
        "fine_location": "I need to know exactly where you are",
        "background_location": "I need to know where you are constantly",
        "photo_library": "I need to see your photos",
        # Custom permissions
        "DUMMY_sit": "I can't sit without an invitation",
        "DUMMY.leave.the.dinner.table": "It would be impolite.",
    }
    myapp.request = {"tasty.beverage": True}

    # In the final context, all cross-platform permissions have been converted to upper
    # case, prefixed with "DUMMY", and moved to the `permissions` key. Custom
    # permissions have been moved to the "custom_permissions" key
    full_context["permissions"] = {
        "DUMMY_CAMERA": "I NEED TO SEE YOU",
        "DUMMY_MICROPHONE": "I NEED TO HEAR YOU",
        "DUMMY_COARSE_LOCATION": "I NEED TO KNOW APPROXIMATELY WHERE YOU ARE",
        "DUMMY_FINE_LOCATION": "I NEED TO KNOW EXACTLY WHERE YOU ARE",
        "DUMMY_BACKGROUND_LOCATION": "I NEED TO KNOW WHERE YOU ARE CONSTANTLY",
        "DUMMY_PHOTO_LIBRARY": "I NEED TO SEE YOUR PHOTOS",
    }
    full_context["custom_permissions"] = {
        "DUMMY_sit": "I can't sit without an invitation",
        "DUMMY.leave.the.dinner.table": "It would be impolite.",
    }

    # An extra request has been added because of the camera permission, and the
    # custom request has been preserved.
    full_context["requests"] = {
        "good.lighting": True,
        "tasty.beverage": True,
    }

    # There won't be a cookiecutter cache, so there won't be
    # a cache path (yet).
    create_command.tools.git.Repo.side_effect = git_exceptions.NoSuchPathError

    # Generate the template.
    create_command.generate_app_template(myapp)

    # Cookiecutter was invoked with the expected template name and context.
    create_command.tools.cookiecutter.assert_called_once_with(
        "https://github.com/beeware/briefcase-Tester-Dummy-template.git",
        no_input=True,
        checkout="v37.42.7",
        output_dir=os.fsdecode(tmp_path / "base_path/build/my-app/tester"),
        extra_context=full_context,
    )
