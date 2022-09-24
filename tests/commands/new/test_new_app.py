import os
from unittest import mock

import pytest
from cookiecutter import exceptions as cookiecutter_exceptions
from cookiecutter.main import cookiecutter

import briefcase
from briefcase.commands import NewCommand
from briefcase.commands.base import (
    InvalidTemplateRepository,
    TemplateUnsupportedVersion,
)
from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError


@pytest.fixture
def new_command(tmp_path):
    return NewCommand(base_path=tmp_path, logger=Log(), console=Console())


@pytest.mark.parametrize(
    "briefcase_version, expected_branch",
    [
        ("37.42.1", "v37.42.1"),
        ("37.42.2.dev73+gad61a29.d20220919", "v37.42.2"),
        ("37.42.3a1", "v37.42.3"),
        ("37.42.4b2", "v37.42.4"),
        ("37.42.5rc3", "v37.42.5"),
        ("37.42.6.post1", "v37.42.6"),
    ],
)
def test_new_app(
    monkeypatch,
    new_command,
    tmp_path,
    briefcase_version,
    expected_branch,
):
    """A new app can be created with the default template."""
    monkeypatch.setattr(briefcase, "__version__", briefcase_version)
    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
    }
    new_command.build_app_context = mock.MagicMock(return_value=app_context)
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="~/.cookiecutters/briefcase-template"
    )
    new_command.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)

    # Create the new app, using the default template.
    new_command.new_app()

    # App context is constructed
    new_command.build_app_context.assert_called_once_with()
    # Template is updated
    new_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://github.com/beeware/briefcase-template",
        branch=expected_branch,
    )
    # Cookiecutter is invoked
    new_command.tools.cookiecutter.assert_called_once_with(
        "~/.cookiecutters/briefcase-template",
        no_input=True,
        output_dir=os.fsdecode(tmp_path),
        checkout=expected_branch,
        extra_context=app_context,
    )


def test_new_app_missing_template(monkeypatch, new_command, tmp_path):
    """If a versioned branch doesn't exist, an error is raised."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
    }
    new_command.build_app_context = mock.MagicMock(return_value=app_context)
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="~/.cookiecutters/briefcase-template"
    )
    new_command.tools.cookiecutter = mock.MagicMock()

    # Mock a failed call to cookiecutter when requesting the branch
    new_command.tools.cookiecutter.side_effect = (
        cookiecutter_exceptions.RepositoryCloneFailed
    )

    # Create the new app, using the default template. This raises an error.
    with pytest.raises(TemplateUnsupportedVersion):
        new_command.new_app()

    # App context is constructed
    new_command.build_app_context.assert_called_once_with()

    # The cookiecutter cache is updated once
    new_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://github.com/beeware/briefcase-template",
        branch="v37.42.7",
    )

    # Cookiecutter is invoked twice
    new_command.tools.cookiecutter.assert_called_once_with(
        "~/.cookiecutters/briefcase-template",
        no_input=True,
        output_dir=os.fsdecode(tmp_path),
        checkout="v37.42.7",
        extra_context=app_context,
    )


def test_new_app_dev(monkeypatch, new_command, tmp_path):
    """In a dev version, template will fall back to the 'main' branch if a
    versioned template doesn't exist."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7.dev73+gad61a29.d20220919")
    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
    }
    new_command.build_app_context = mock.MagicMock(return_value=app_context)
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="~/.cookiecutters/briefcase-template"
    )
    new_command.tools.cookiecutter = mock.MagicMock()

    # There will be two calls to cookiecutter; one on the versioned branch,
    # and one on the `main` branch. The first call will fail because the
    # template doesn't exist yet; the second will succeed.
    new_command.tools.cookiecutter.side_effect = [
        cookiecutter_exceptions.RepositoryCloneFailed,
        None,
    ]

    # Create the new app, using the default template.
    new_command.new_app()

    # App context is constructed
    new_command.build_app_context.assert_called_once_with()
    # Template is updated
    assert new_command.update_cookiecutter_cache.mock_calls == [
        mock.call(
            template="https://github.com/beeware/briefcase-template",
            branch="v37.42.7",
        ),
        mock.call(
            template="https://github.com/beeware/briefcase-template",
            branch="main",
        ),
    ]

    # Cookiecutter is invoked twice
    new_command.tools.cookiecutter.assert_has_calls(
        [
            mock.call(
                "~/.cookiecutters/briefcase-template",
                no_input=True,
                output_dir=os.fsdecode(tmp_path),
                checkout="v37.42.7",
                extra_context=app_context,
            ),
            mock.call(
                "~/.cookiecutters/briefcase-template",
                no_input=True,
                output_dir=os.fsdecode(tmp_path),
                checkout="main",
                extra_context=app_context,
            ),
        ]
    )


def test_new_app_with_template(monkeypatch, new_command, tmp_path):
    """A specific template can be requested."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")

    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
    }
    new_command.build_app_context = mock.MagicMock(return_value=app_context)
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="https://example.com/other.git"
    )
    new_command.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)

    # Create a new app, with a specific template.
    new_command.new_app(template="https://example.com/other.git")

    # App context is constructed
    new_command.build_app_context.assert_called_once_with()
    # Template is updated
    new_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/other.git",
        branch="v37.42.7",
    )
    # Cookiecutter is invoked
    new_command.tools.cookiecutter.assert_called_once_with(
        "https://example.com/other.git",
        no_input=True,
        output_dir=os.fsdecode(tmp_path),
        checkout="v37.42.7",
        extra_context=app_context,
    )


def test_new_app_with_invalid_template(monkeypatch, new_command, tmp_path):
    """If the custom template is invalid, an error is raised."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")

    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
    }
    new_command.build_app_context = mock.MagicMock(return_value=app_context)
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="https://example.com/other.git"
    )
    new_command.tools.cookiecutter = mock.MagicMock()

    # Mock an error due to a missing repository
    new_command.tools.cookiecutter.side_effect = (
        cookiecutter_exceptions.RepositoryNotFound
    )

    # Create a new app, with a specific template.
    with pytest.raises(InvalidTemplateRepository):
        new_command.new_app(template="https://example.com/other.git")

    # App context is constructed
    new_command.build_app_context.assert_called_once_with()
    # Template is updated
    new_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/other.git",
        branch="v37.42.7",
    )
    # Cookiecutter is invoked
    new_command.tools.cookiecutter.assert_called_once_with(
        "https://example.com/other.git",
        no_input=True,
        output_dir=os.fsdecode(tmp_path),
        checkout="v37.42.7",
        extra_context=app_context,
    )


def test_new_app_with_invalid_template_branch(monkeypatch, new_command, tmp_path):
    """If the custom template doesn't have a branch for the version, an error
    is raised."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")

    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
    }
    new_command.build_app_context = mock.MagicMock(return_value=app_context)
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="https://example.com/other.git"
    )
    new_command.tools.cookiecutter = mock.MagicMock()

    # Mock the error when the branch doesn't exist
    new_command.tools.cookiecutter.side_effect = (
        cookiecutter_exceptions.RepositoryCloneFailed
    )

    # Create a new app, with a specific template; this raises an error
    with pytest.raises(TemplateUnsupportedVersion):
        new_command.new_app(template="https://example.com/other.git")

    # App context is constructed
    new_command.build_app_context.assert_called_once_with()

    # Template is updated
    new_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/other.git",
        branch="v37.42.7",
    )

    # Cookiecutter is invoked
    new_command.tools.cookiecutter.assert_called_once_with(
        "https://example.com/other.git",
        no_input=True,
        output_dir=os.fsdecode(tmp_path),
        checkout="v37.42.7",
        extra_context=app_context,
    )


def test_abort_if_directory_exists(monkeypatch, new_command, tmp_path):
    """If the application name directory exists, the create aborts."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")

    # Create a colliding app name.
    (tmp_path / "myapplication").mkdir()

    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
    }
    new_command.build_app_context = mock.MagicMock(return_value=app_context)
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="~/.cookiecutters/briefcase-template"
    )
    new_command.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)

    # Create the new app, using the default template.
    # This will raise an error due to the colliding directory
    with pytest.raises(BriefcaseCommandError):
        new_command.new_app()

    # App context is constructed
    new_command.build_app_context.assert_called_once_with()
    # Template won't be updated or unrolled
    # Cookiecutter was *not* invoked
    new_command.update_cookiecutter_cache.call_count == 0
    assert new_command.tools.cookiecutter.call_count == 0
