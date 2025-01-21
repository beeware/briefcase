import os
from unittest import mock

import pytest
from cookiecutter import exceptions as cookiecutter_exceptions
from cookiecutter.main import cookiecutter

import briefcase
from briefcase.bootstraps import BaseGuiBootstrap
from briefcase.commands import NewCommand
from briefcase.console import Console
from briefcase.exceptions import (
    BriefcaseCommandError,
    InvalidTemplateBranch,
    InvalidTemplateRepository,
)


@pytest.fixture
def new_command(tmp_path):
    return NewCommand(
        base_path=tmp_path / "base",
        data_path=tmp_path / "data",
        console=Console(),
    )


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
    bootstrap = BaseGuiBootstrap(new_command.console, {})
    bootstrap.post_generate = mock.MagicMock()
    new_command.create_bootstrap = mock.MagicMock(return_value=bootstrap)
    new_command.build_gui_context = mock.MagicMock(
        return_value={
            "app_source": "main()",
            "pyproject_requires": "toga",
        }
    )
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="~/.cookiecutters/briefcase-template"
    )
    new_command.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)

    # Create the new app, using the default template and no project overrides
    new_command.new_app(project_overrides={})

    # App context is constructed
    new_command.build_app_context.assert_called_once_with({})
    new_command.create_bootstrap.assert_called_once_with(app_context, {})
    new_command.build_gui_context.assert_called_once_with(bootstrap, {})

    # Template is updated
    new_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://github.com/beeware/briefcase-template",
        branch=expected_branch,
    )
    # Cookiecutter is invoked
    new_command.tools.cookiecutter.assert_called_once_with(
        "~/.cookiecutters/briefcase-template",
        no_input=True,
        output_dir=os.fsdecode(tmp_path / "base"),
        checkout=expected_branch,
        extra_context={
            "formal_name": "My Application",
            "class_name": "MyApplication",
            "app_name": "myapplication",
            # The expected app context
            # should now also contain the
            # default template and branch
            "template_source": "https://github.com/beeware/briefcase-template",
            "template_branch": expected_branch,
            "briefcase_version": briefcase_version,
            "app_source": "main()",
            "pyproject_requires": "toga",
        },
        default_config={"replay_dir": str(tmp_path / "data/templates/.replay")},
    )

    # Bootstrap post-generate step is invoked with correct path
    bootstrap.post_generate.assert_called_once_with(
        base_path=tmp_path / "base" / "myapplication"
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
    bootstrap = BaseGuiBootstrap(new_command.console, {})
    new_command.create_bootstrap = mock.MagicMock(return_value=bootstrap)
    new_command.build_gui_context = mock.MagicMock(
        return_value={
            "app_source": "main()",
            "pyproject_requires": "toga",
        }
    )
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="~/.cookiecutters/briefcase-template"
    )
    new_command.tools.cookiecutter = mock.MagicMock()

    # Mock a failed call to cookiecutter when requesting the branch
    new_command.tools.cookiecutter.side_effect = (
        cookiecutter_exceptions.RepositoryCloneFailed
    )

    # Create the new app, using the default template. This raises an error.
    with pytest.raises(InvalidTemplateBranch):
        new_command.new_app(project_overrides={})

    # App context is constructed
    new_command.build_app_context.assert_called_once_with({})
    new_command.create_bootstrap.assert_called_once_with(app_context, {})
    new_command.build_gui_context.assert_called_once_with(bootstrap, {})

    # The cookiecutter cache is updated once
    new_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://github.com/beeware/briefcase-template",
        branch="v37.42.7",
    )

    # Cookiecutter is invoked twice
    new_command.tools.cookiecutter.assert_called_once_with(
        "~/.cookiecutters/briefcase-template",
        no_input=True,
        output_dir=os.fsdecode(tmp_path / "base"),
        checkout="v37.42.7",
        extra_context={
            "formal_name": "My Application",
            "class_name": "MyApplication",
            "app_name": "myapplication",
            # The expected app context
            # should now also contain the
            # default template and branch
            "template_source": "https://github.com/beeware/briefcase-template",
            "template_branch": "v37.42.7",
            "briefcase_version": "37.42.7",
            "app_source": "main()",
            "pyproject_requires": "toga",
        },
        default_config={"replay_dir": str(tmp_path / "data/templates/.replay")},
    )


@pytest.mark.parametrize(
    "briefcase_version",
    ("37.42.7.dev0+gad61a29.d20220919", "37.42.7.dev73+gad61a29.d20220919"),
)
def test_new_app_dev(monkeypatch, new_command, tmp_path, briefcase_version):
    """In a dev version, template will fall back to the 'main' branch if a versioned
    template doesn't exist."""
    monkeypatch.setattr(briefcase, "__version__", briefcase_version)
    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
    }
    new_command.build_app_context = mock.MagicMock(return_value=app_context)
    bootstrap = BaseGuiBootstrap(new_command.console, {})
    new_command.create_bootstrap = mock.MagicMock(return_value=bootstrap)
    new_command.build_gui_context = mock.MagicMock(
        return_value={
            "app_source": "main()",
            "pyproject_requires": "toga",
        }
    )
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

    # Create the new app, using the default template and no project overrides.
    new_command.new_app(project_overrides={})

    # App context is constructed
    new_command.build_app_context.assert_called_once_with({})
    new_command.create_bootstrap.assert_called_once_with(app_context, {})
    new_command.build_gui_context.assert_called_once_with(bootstrap, {})

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
                output_dir=os.fsdecode(tmp_path / "base"),
                checkout="v37.42.7",
                extra_context={
                    "formal_name": "My Application",
                    "class_name": "MyApplication",
                    "app_name": "myapplication",
                    # The expected app context should now also contain the default
                    # template and branch
                    "template_source": "https://github.com/beeware/briefcase-template",
                    "template_branch": "v37.42.7",
                    "briefcase_version": briefcase_version,
                    "app_source": "main()",
                    "pyproject_requires": "toga",
                },
                default_config={"replay_dir": str(tmp_path / "data/templates/.replay")},
            ),
            mock.call(
                "~/.cookiecutters/briefcase-template",
                no_input=True,
                output_dir=os.fsdecode(tmp_path / "base"),
                checkout="main",
                extra_context={
                    "formal_name": "My Application",
                    "class_name": "MyApplication",
                    "app_name": "myapplication",
                    # The expected app context should now also contain the default
                    # template and branch
                    "template_source": "https://github.com/beeware/briefcase-template",
                    "template_branch": "main",
                    "briefcase_version": briefcase_version,
                    "app_source": "main()",
                    "pyproject_requires": "toga",
                },
                default_config={"replay_dir": str(tmp_path / "data/templates/.replay")},
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
    bootstrap = BaseGuiBootstrap(new_command.console, {})
    new_command.create_bootstrap = mock.MagicMock(return_value=bootstrap)
    new_command.build_gui_context = mock.MagicMock(
        return_value={
            "app_source": "main()",
            "pyproject_requires": "toga",
        }
    )
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="https://example.com/other.git"
    )
    new_command.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)

    # Create a new app, with a specific template and no project overrides
    new_command.new_app(template="https://example.com/other.git", project_overrides={})

    # App context is constructed
    new_command.build_app_context.assert_called_once_with({})
    new_command.create_bootstrap.assert_called_once_with(app_context, {})
    new_command.build_gui_context.assert_called_once_with(bootstrap, {})

    # Template is updated
    new_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/other.git",
        branch="v37.42.7",
    )
    # Cookiecutter is invoked
    new_command.tools.cookiecutter.assert_called_once_with(
        "https://example.com/other.git",
        no_input=True,
        output_dir=os.fsdecode(tmp_path / "base"),
        checkout="v37.42.7",
        extra_context={
            "formal_name": "My Application",
            "class_name": "MyApplication",
            "app_name": "myapplication",
            # The expected app context
            # should now also contain the
            # template and branch
            "template_source": "https://example.com/other.git",
            "template_branch": "v37.42.7",
            "briefcase_version": "37.42.7",
            "app_source": "main()",
            "pyproject_requires": "toga",
        },
        default_config={"replay_dir": str(tmp_path / "data/templates/.replay")},
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
    bootstrap = BaseGuiBootstrap(new_command.console, {})
    new_command.create_bootstrap = mock.MagicMock(return_value=bootstrap)
    new_command.build_gui_context = mock.MagicMock(
        return_value={
            "app_source": "main()",
            "pyproject_requires": "toga",
        }
    )
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="https://example.com/other.git"
    )
    new_command.tools.cookiecutter = mock.MagicMock()

    # Mock an error due to a missing repository
    new_command.tools.cookiecutter.side_effect = (
        cookiecutter_exceptions.RepositoryNotFound
    )

    # Create a new app, with a specific template and no project overrides
    with pytest.raises(InvalidTemplateRepository):
        new_command.new_app(
            template="https://example.com/other.git",
            project_overrides={},
        )

    # App context is constructed
    new_command.build_app_context.assert_called_once_with({})
    new_command.create_bootstrap.assert_called_once_with(app_context, {})
    new_command.build_gui_context.assert_called_once_with(bootstrap, {})

    # Template is updated
    new_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/other.git",
        branch="v37.42.7",
    )
    # Cookiecutter is invoked
    new_command.tools.cookiecutter.assert_called_once_with(
        "https://example.com/other.git",
        no_input=True,
        output_dir=os.fsdecode(tmp_path / "base"),
        checkout="v37.42.7",
        extra_context={
            "formal_name": "My Application",
            "class_name": "MyApplication",
            "app_name": "myapplication",
            # The expected app context
            # should now also contain the
            # template and branch
            "template_source": "https://example.com/other.git",
            "template_branch": "v37.42.7",
            "briefcase_version": "37.42.7",
            "app_source": "main()",
            "pyproject_requires": "toga",
        },
        default_config={"replay_dir": str(tmp_path / "data/templates/.replay")},
    )


def test_new_app_with_invalid_template_branch(monkeypatch, new_command, tmp_path):
    """If the custom template doesn't have a branch for the version, an error is
    raised."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
    }
    new_command.build_app_context = mock.MagicMock(return_value=app_context)
    bootstrap = BaseGuiBootstrap(new_command.console, {})
    new_command.create_bootstrap = mock.MagicMock(return_value=bootstrap)
    new_command.build_gui_context = mock.MagicMock(
        return_value={
            "app_source": "main()",
            "pyproject_requires": "toga",
        }
    )
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="https://example.com/other.git"
    )
    new_command.tools.cookiecutter = mock.MagicMock()

    # Mock the error when the branch doesn't exist
    new_command.tools.cookiecutter.side_effect = (
        cookiecutter_exceptions.RepositoryCloneFailed
    )

    # Create a new app, with a specific template; this raises an error
    with pytest.raises(InvalidTemplateBranch):
        new_command.new_app(
            template="https://example.com/other.git",
            project_overrides={},
        )

    # App context is constructed
    new_command.build_app_context.assert_called_once_with({})
    new_command.create_bootstrap.assert_called_once_with(app_context, {})
    new_command.build_gui_context.assert_called_once_with(bootstrap, {})

    # Template is updated
    new_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/other.git",
        branch="v37.42.7",
    )

    # Cookiecutter is invoked
    new_command.tools.cookiecutter.assert_called_once_with(
        "https://example.com/other.git",
        no_input=True,
        output_dir=os.fsdecode(tmp_path / "base"),
        checkout="v37.42.7",
        extra_context={
            "formal_name": "My Application",
            "class_name": "MyApplication",
            "app_name": "myapplication",
            # The expected app context
            # should now also contain the
            # template and branch
            "template_source": "https://example.com/other.git",
            "template_branch": "v37.42.7",
            "briefcase_version": "37.42.7",
            "app_source": "main()",
            "pyproject_requires": "toga",
        },
        default_config={"replay_dir": str(tmp_path / "data/templates/.replay")},
    )


def test_new_app_with_branch(monkeypatch, new_command, tmp_path):
    """A specific branch can be requested."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
    }
    new_command.build_app_context = mock.MagicMock(return_value=app_context)
    bootstrap = BaseGuiBootstrap(new_command.console, {})
    new_command.create_bootstrap = mock.MagicMock(return_value=bootstrap)
    new_command.build_gui_context = mock.MagicMock(
        return_value={
            "app_source": "main()",
            "pyproject_requires": "toga",
        }
    )
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="https://example.com/other.git"
    )
    new_command.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)

    # Create a new app, with a specific template branch.
    new_command.new_app(template_branch="experimental", project_overrides={})

    # App context is constructed
    new_command.build_app_context.assert_called_once_with({})
    new_command.create_bootstrap.assert_called_once_with(app_context, {})
    new_command.build_gui_context.assert_called_once_with(bootstrap, {})

    # Template is updated
    new_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://github.com/beeware/briefcase-template",
        branch="experimental",
    )
    # Cookiecutter is invoked
    new_command.tools.cookiecutter.assert_called_once_with(
        "https://example.com/other.git",
        no_input=True,
        output_dir=os.fsdecode(tmp_path / "base"),
        checkout="experimental",
        extra_context={
            "formal_name": "My Application",
            "class_name": "MyApplication",
            "app_name": "myapplication",
            # The expected app context
            # should now also contain the
            # template and branch
            "template_source": "https://github.com/beeware/briefcase-template",
            "template_branch": "experimental",
            "briefcase_version": "37.42.7",
            "app_source": "main()",
            "pyproject_requires": "toga",
        },
        default_config={"replay_dir": str(tmp_path / "data/templates/.replay")},
    )


def test_new_app_unused_project_overrides(
    monkeypatch,
    new_command,
    tmp_path,
    capsys,
):
    """The user is informed of unused project configuration overrides."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")
    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
    }
    new_command.build_app_context = mock.MagicMock(return_value=app_context)
    bootstrap = BaseGuiBootstrap(new_command.console, {})
    new_command.create_bootstrap = mock.MagicMock(return_value=bootstrap)
    new_command.build_gui_context = mock.MagicMock(
        return_value={
            "app_source": "main()",
            "pyproject_requires": "toga",
        }
    )
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="~/.cookiecutters/briefcase-template"
    )
    new_command.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)

    # Create the new app, using the default template.
    new_command.new_app(project_overrides={"unused": "override"})

    # App context is constructed
    new_command.build_app_context.assert_called_once_with({"unused": "override"})
    new_command.create_bootstrap.assert_called_once_with(
        app_context, {"unused": "override"}
    )
    new_command.build_gui_context.assert_called_once_with(
        bootstrap, {"unused": "override"}
    )
    # Template is updated
    new_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://github.com/beeware/briefcase-template",
        branch="v37.42.7",
    )
    # Cookiecutter is invoked
    new_command.tools.cookiecutter.assert_called_once_with(
        "~/.cookiecutters/briefcase-template",
        no_input=True,
        output_dir=os.fsdecode(tmp_path / "base"),
        checkout="v37.42.7",
        extra_context={
            "formal_name": "My Application",
            "class_name": "MyApplication",
            "app_name": "myapplication",
            # The expected app context
            # should now also contain the
            # default template and branch
            "template_source": "https://github.com/beeware/briefcase-template",
            "template_branch": "v37.42.7",
            "briefcase_version": "37.42.7",
            "app_source": "main()",
            "pyproject_requires": "toga",
        },
        default_config={"replay_dir": str(tmp_path / "data/templates/.replay")},
    )

    unused_project_override_warning = (
        "WARNING: These project configuration overrides were not used:\n\n"
        "    unused = override"
    )
    assert unused_project_override_warning in capsys.readouterr().out


def test_abort_if_directory_exists(monkeypatch, new_command, tmp_path):
    """If the application name directory exists, the create aborts."""
    monkeypatch.setattr(briefcase, "__version__", "37.42.7")

    # Create a colliding app name.
    (tmp_path / "base/myapplication").mkdir(parents=True)

    app_context = {
        "formal_name": "My Application",
        "class_name": "MyApplication",
        "app_name": "myapplication",
    }
    new_command.build_app_context = mock.MagicMock(return_value=app_context)
    bootstrap = BaseGuiBootstrap(new_command.console, {})
    new_command.create_bootstrap = mock.MagicMock(return_value=bootstrap)
    new_command.build_gui_context = mock.MagicMock(
        return_value={
            "app_source": "main()",
            "pyproject_requires": "toga",
        }
    )
    new_command.update_cookiecutter_cache = mock.MagicMock(
        return_value="~/.cookiecutters/briefcase-template"
    )
    new_command.tools.cookiecutter = mock.MagicMock(spec_set=cookiecutter)

    # Create the new app, using the default template.
    # This will raise an error due to the colliding directory
    with pytest.raises(BriefcaseCommandError):
        new_command.new_app(project_overrides={})

    # App context is constructed
    new_command.build_app_context.assert_called_once_with({})
    new_command.create_bootstrap.assert_called_once_with(app_context, {})
    new_command.build_gui_context.assert_called_once_with(bootstrap, {})

    # Template won't be updated or unrolled
    # Cookiecutter was *not* invoked
    assert new_command.update_cookiecutter_cache.call_count == 0
    assert new_command.tools.cookiecutter.call_count == 0
