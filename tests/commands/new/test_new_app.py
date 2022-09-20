import os
from unittest import mock

import pytest
from cookiecutter import exceptions as cookiecutter_exceptions

import briefcase
from briefcase.commands import NewCommand
from briefcase.exceptions import BriefcaseCommandError


@pytest.fixture
def new_command(tmp_path):
    return NewCommand(base_path=tmp_path)


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
    new_command.cookiecutter = mock.MagicMock()

    # Create the new app, using the default template.
    new_command.new_app()

    # App context is constructed
    new_command.build_app_context.assert_called_with()
    # Template is updated
    new_command.update_cookiecutter_cache.assert_called_with(
        template="https://github.com/beeware/briefcase-template",
        branch=expected_branch,
    )
    # Cookiecutter is invoked
    new_command.cookiecutter.assert_called_with(
        "~/.cookiecutters/briefcase-template",
        no_input=True,
        output_dir=os.fsdecode(tmp_path),
        checkout=expected_branch,
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
    new_command.cookiecutter = mock.MagicMock()

    # There will be two calls to cookiecutter; one on the versioned branch,
    # and one on the `main` branch. The first call will fail because the
    # template doesn't exist yet; the second will succeed.
    new_command.cookiecutter.side_effect = [
        cookiecutter_exceptions.RepositoryCloneFailed,
        None,
    ]

    # Create the new app, using the default template.
    new_command.new_app()

    # App context is constructed
    new_command.build_app_context.assert_called_with()
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
    new_command.cookiecutter.assert_has_calls(
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
    new_command.cookiecutter = mock.MagicMock()

    # Create a new app, with a specific template.
    new_command.new_app(template="https://example.com/other.git")

    # App context is constructed
    new_command.build_app_context.assert_called_with()
    # Template is updated
    new_command.update_cookiecutter_cache.assert_called_with(
        template="https://example.com/other.git",
        branch="v37.42.7",
    )
    # Cookiecutter is invoked
    new_command.cookiecutter.assert_called_with(
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
    new_command.cookiecutter = mock.MagicMock()

    # Create the new app, using the default template.
    # This will raise an error due to the colliding directory
    with pytest.raises(BriefcaseCommandError):
        new_command.new_app()

    # App context is constructed
    new_command.build_app_context.assert_called_with()
    # Template won't be updated or unrolled
    # Cookiecutter was *not* invoked
    new_command.update_cookiecutter_cache.call_count == 0
    new_command.cookiecutter.call_count == 0
