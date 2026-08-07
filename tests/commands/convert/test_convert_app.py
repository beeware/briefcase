import os
from unittest import mock

import pytest
from cookiecutter.main import cookiecutter

import briefcase
from briefcase.commands import ConvertCommand


@pytest.fixture
def convert_command(dummy_console, tmp_path):
    return ConvertCommand(
        console=dummy_console,
        base_path=tmp_path / "project",
        data_path=tmp_path / "data",
    )


def test_convert_app_unused_project_overrides(
    monkeypatch,
    convert_command,
    tmp_path,
    capsys,
):
    """The user is informed of unused project configuration overrides."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
        "module_name": "mymodule",
        "test_source_dir": "test_files",
    }
    convert_command.build_app_context = mock.MagicMock(return_value=app_context)
    convert_command.build_gui_context = mock.MagicMock(
        return_value={"gui_framework": "None"}
    )
    convert_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="~/.cookiecutters/briefcase-template"
    )
    convert_command.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)
    convert_command.migrate_necessary_files = mock.MagicMock()

    # Create the new app, using the default template.
    convert_command.convert_app(
        tmp_path=tmp_path / "working",
        project_overrides={"unused": "override"},
    )

    # App context is constructed
    convert_command.build_app_context.assert_called_once_with({"unused": "override"})
    convert_command.build_gui_context.assert_called_once_with(
        mock.ANY, {"unused": "override"}
    )
    # Template is updated, and its hash is verified
    convert_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://github.com/beeware/briefcase-template",
        branch="v37.42.7",
        template_hash=convert_command.template_hash,
    )
    # Cookiecutter is invoked
    convert_command.tools.cookiecutter.assert_called_once_with(
        "~/.cookiecutters/briefcase-template",
        no_input=True,
        output_dir=os.fsdecode(tmp_path / "working"),
        checkout="v37.42.7",
        extra_context={
            "formal_name": "My Application",
            "class_name": "MyApplication",
            "app_name": "myapplication",
            "module_name": "mymodule",
            "test_source_dir": "test_files",
            # The expected app context should now also contain the default template,
            # branch, and Briefcase version.
            "template_source": "https://github.com/beeware/briefcase-template",
            "template_branch": "v37.42.7",
            "briefcase_version": "37.42.7",
            "gui_framework": "None",
        },
        default_config={"replay_dir": str(tmp_path / "data/templates/.replay")},
    )
    convert_command.migrate_necessary_files.assert_called_once_with(
        tmp_path / "working" / app_context["app_name"],
        app_context["test_source_dir"],
        "mymodule",
    )

    unused_project_override_warning = (
        "WARNING: These project configuration overrides were not used:\n\n"
        "    unused = override"
    )
    assert unused_project_override_warning in capsys.readouterr().out


def test_convert_app_with_template(
    monkeypatch,
    convert_command,
    tmp_path,
    capsys,
):
    """If a custom template is requested without a matching hash, a warning is
    logged."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
        "module_name": "mymodule",
        "test_source_dir": "test_files",
    }
    convert_command.build_app_context = mock.MagicMock(return_value=app_context)
    convert_command.build_gui_context = mock.MagicMock(
        return_value={"gui_framework": "None"}
    )
    convert_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="https://example.com/other.git"
    )
    convert_command.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)
    convert_command.migrate_necessary_files = mock.MagicMock()

    convert_command.convert_app(
        tmp_path=tmp_path / "working",
        template="https://example.com/other.git",
        project_overrides={},
    )

    convert_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/other.git",
        branch="v37.42.7",
        template_hash=None,
    )


def test_convert_app_with_template_and_hash(
    monkeypatch,
    convert_command,
    tmp_path,
    capsys,
):
    """If a custom template is requested with a hash, content is verified."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
        "module_name": "mymodule",
        "test_source_dir": "test_files",
    }
    convert_command.build_app_context = mock.MagicMock(return_value=app_context)
    convert_command.build_gui_context = mock.MagicMock(
        return_value={"gui_framework": "None"}
    )
    convert_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="https://example.com/other.git"
    )
    convert_command.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)
    convert_command.migrate_necessary_files = mock.MagicMock()

    convert_command.convert_app(
        tmp_path=tmp_path / "working",
        template="https://example.com/other.git",
        template_hash="sha1:1234567890123456789012345678901234567890",
        project_overrides={},
    )

    convert_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/other.git",
        branch="v37.42.7",
        template_hash="sha1:1234567890123456789012345678901234567890",
    )


def test_convert_app_with_branch(
    monkeypatch,
    convert_command,
    tmp_path,
    capsys,
):
    """If a custom template branch is requested without a matching hash, a warning is
    logged."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
        "module_name": "mymodule",
        "test_source_dir": "test_files",
    }
    convert_command.build_app_context = mock.MagicMock(return_value=app_context)
    convert_command.build_gui_context = mock.MagicMock(
        return_value={"gui_framework": "None"}
    )
    convert_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="~/.cookiecutters/briefcase-template"
    )
    convert_command.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)
    convert_command.migrate_necessary_files = mock.MagicMock()

    convert_command.convert_app(
        tmp_path=tmp_path / "working",
        template_branch="experimental",
        project_overrides={},
    )

    convert_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://github.com/beeware/briefcase-template",
        branch="experimental",
        template_hash=None,
    )


def test_convert_app_with_branch_and_hash(
    monkeypatch,
    convert_command,
    tmp_path,
    capsys,
):
    """If a custom template is requested with a hash, content is verified."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
        "module_name": "mymodule",
        "test_source_dir": "test_files",
    }
    convert_command.build_app_context = mock.MagicMock(return_value=app_context)
    convert_command.build_gui_context = mock.MagicMock(
        return_value={"gui_framework": "None"}
    )
    convert_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="~/.cookiecutters/briefcase-template"
    )
    convert_command.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)
    convert_command.migrate_necessary_files = mock.MagicMock()

    convert_command.convert_app(
        tmp_path=tmp_path / "working",
        template_branch="experimental",
        template_hash="sha1:1234567890123456789012345678901234567890",
        project_overrides={},
    )

    convert_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://github.com/beeware/briefcase-template",
        branch="experimental",
        template_hash="sha1:1234567890123456789012345678901234567890",
    )


def test_convert_app_with_all_template_details(
    monkeypatch,
    convert_command,
    tmp_path,
    capsys,
):
    """If a custom template and branch is requested with a hash, content is verified."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
        "module_name": "mymodule",
        "test_source_dir": "test_files",
    }
    convert_command.build_app_context = mock.MagicMock(return_value=app_context)
    convert_command.build_gui_context = mock.MagicMock(
        return_value={"gui_framework": "None"}
    )
    convert_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="~/.cookiecutters/briefcase-template"
    )
    convert_command.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)
    convert_command.migrate_necessary_files = mock.MagicMock()

    convert_command.convert_app(
        tmp_path=tmp_path / "working",
        template="https://example.com/other.git",
        template_branch="experimental",
        template_hash="sha1:1234567890123456789012345678901234567890",
        project_overrides={},
    )

    convert_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/other.git",
        branch="experimental",
        template_hash="sha1:1234567890123456789012345678901234567890",
    )
