import os
from unittest import mock

import pytest
from cookiecutter.main import cookiecutter

import briefcase
from briefcase.commands import ConvertCommand
from briefcase.console import Console, Log


@pytest.fixture
def convert_command(tmp_path):
    return ConvertCommand(
        base_path=tmp_path / "project", logger=Log(), console=Console()
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
        app_context, {"unused": "override"}
    )
    # Template is updated
    convert_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://github.com/beeware/briefcase-template",
        branch="v37.42.7",
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
