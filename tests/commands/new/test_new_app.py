import os
from unittest import mock

import pytest

import briefcase
from briefcase.commands import NewCommand
from briefcase.exceptions import BriefcaseCommandError


@pytest.fixture
def new_command(tmp_path):
    return NewCommand(base_path=tmp_path)


@pytest.mark.parametrize(
    "briefcase_version",
    [
        "37.42.7",
        "37.42.7.dev73+gad61a29.d20220919",
        "37.42.7a1",
        "37.42.7b2",
        "37.42.7rc3",
        "37.42.7.post1",
    ],
)
def test_new_app(monkeypatch, new_command, tmp_path, briefcase_version):
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
        branch="v37.42.7",
    )
    # Cookiecutter is invoked
    new_command.cookiecutter.assert_called_with(
        "~/.cookiecutters/briefcase-template",
        no_input=True,
        output_dir=os.fsdecode(tmp_path),
        checkout="v37.42.7",
        extra_context=app_context,
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
    # Template is updated
    new_command.update_cookiecutter_cache.assert_called_with(
        template="https://github.com/beeware/briefcase-template",
        branch="v37.42.7",
    )
    # Cookiecutter was *not* invoked
    new_command.cookiecutter.call_count == 0
