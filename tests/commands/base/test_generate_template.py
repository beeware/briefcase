import subprocess
from pathlib import Path
from unittest import mock

import pytest
from cookiecutter import exceptions as cookiecutter_exceptions
from packaging.version import Version

import briefcase
from briefcase.exceptions import (
    BriefcaseConfigError,
    InvalidTemplateBranch,
    InvalidTemplateRepository,
    NetworkFailure,
)

from ...utils import create_json_file


@pytest.fixture
def base_command(base_command, tmp_path):
    template_path = tmp_path / ".cookiecutters/template"

    # Mock templating commands; ensure that a cookiecutter.json is created
    base_command.update_cookiecutter_cache = mock.MagicMock(return_value=template_path)
    base_command.tools.cookiecutter = mock.MagicMock()

    return base_command


def test_default_branch(base_command, tmp_path):
    """A template clone can use the default branch."""

    extra_context = {"extra1": 37, "extra2": 42}
    template_path = base_command.generate_template(
        template="https://example.com/template",
        branch=None,
        output_path=tmp_path / "output",
        extra_context=extra_context,
        template_hash="deadbeef",
    )

    template_branch = f"v{Version(briefcase.__version__).base_version}"
    # Template cache is updated
    base_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/template",
        branch=template_branch,
        template_hash="deadbeef",
    )
    # Cookiecutter is generated
    base_command.tools.cookiecutter.assert_called_once_with(
        str(tmp_path / ".cookiecutters/template"),
        no_input=True,
        output_dir=str(tmp_path / "output"),
        checkout=template_branch,
        extra_context={
            "template_source": "https://example.com/template",
            "template_branch": template_branch,
            "briefcase_version": str(Version(briefcase.__version__)),
            **extra_context,
        },
        default_config={"replay_dir": str(tmp_path / "data_path/templates/.replay")},
    )

    # The context wasn't modified by generating the template
    assert extra_context == {"extra1": 37, "extra2": 42}

    # The cache patch is returned
    assert template_path == tmp_path / ".cookiecutters/template"


def test_explicit_branch(base_command, tmp_path):
    """A template clone can use an explicit branch."""

    extra_context = {"extra1": 37, "extra2": 42}
    template_path = base_command.generate_template(
        template="https://example.com/template",
        branch="special-branch",
        output_path=tmp_path / "output",
        extra_context=extra_context,
        template_hash="deadbeef",
    )

    # Template cache is updated
    base_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/template",
        branch="special-branch",
        template_hash="deadbeef",
    )
    # Cookiecutter is generated
    base_command.tools.cookiecutter.assert_called_once_with(
        str(tmp_path / ".cookiecutters/template"),
        no_input=True,
        output_dir=str(tmp_path / "output"),
        checkout="special-branch",
        extra_context={
            "template_source": "https://example.com/template",
            "template_branch": "special-branch",
            "briefcase_version": str(Version(briefcase.__version__)),
            **extra_context,
        },
        default_config={"replay_dir": str(tmp_path / "data_path/templates/.replay")},
    )

    # The context wasn't modified by generating the template
    assert extra_context == {"extra1": 37, "extra2": 42}

    # The cache patch is returned
    assert template_path == tmp_path / ".cookiecutters/template"


@pytest.mark.parametrize("version", ["0.4.5", "0.4.5.dev0"])
def test_explicit_invalid_branch(monkeypatch, base_command, tmp_path, version):
    """If the explicit branch doesn't exist, an error is raised whether we're in
    dev or not."""
    # Monkeypatch the version
    monkeypatch.setattr(briefcase, "__version__", version)

    # Mock a cookiecutter failure due to a bad template
    base_command.tools.cookiecutter.side_effect = (
        cookiecutter_exceptions.RepositoryCloneFailed
    )

    extra_context = {"extra1": 37, "extra2": 42}
    with pytest.raises(InvalidTemplateBranch):
        base_command.generate_template(
            template="https://example.com/template",
            branch="special-branch",
            output_path=tmp_path / "output",
            extra_context=extra_context,
            template_hash="deadbeef",
        )

    # An attempt was made to update the template cache
    base_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/template",
        branch="special-branch",
        template_hash="deadbeef",
    )
    # An attempt was made to run the cookiecutter
    base_command.tools.cookiecutter.assert_called_once_with(
        str(tmp_path / ".cookiecutters/template"),
        no_input=True,
        output_dir=str(tmp_path / "output"),
        checkout="special-branch",
        extra_context={
            "template_source": "https://example.com/template",
            "template_branch": "special-branch",
            "briefcase_version": str(Version(briefcase.__version__)),
            **extra_context,
        },
        default_config={"replay_dir": str(tmp_path / "data_path/templates/.replay")},
    )


def test_invalid_version_branch_dev(monkeypatch, base_command, tmp_path):
    """If the version branch doesn't exist, and we're in dev, the template
    falls back to the main branch."""
    monkeypatch.setattr(briefcase, "__version__", "0.4.5.dev0")

    # First attempt to clone (on version branch) fails; second succeeds.
    def _mock_cookiecutter(template_path, *args, **kwargs):
        if kwargs["extra_context"]["template_branch"] != "main":
            raise cookiecutter_exceptions.RepositoryCloneFailed()
        create_json_file(
            Path(template_path) / "cookiecutter.json",
            {"pork": "ham", "spam": "?"},
        )

    base_command.tools.cookiecutter.side_effect = _mock_cookiecutter

    extra_context = {"extra1": 37, "extra2": 42}
    template_path = base_command.generate_template(
        template="https://example.com/template",
        branch=None,
        output_path=tmp_path / "output",
        extra_context=extra_context,
        template_hash="deadbeef",
    )

    # Two attempts were made to update the template cache
    assert base_command.update_cookiecutter_cache.mock_calls == [
        mock.call(
            template="https://example.com/template",
            branch="v0.4.5",
            template_hash="deadbeef",
        ),
        mock.call(
            template="https://example.com/template",
            branch="main",
            template_hash=None,
        ),
    ]

    # Two attempts were made to generate the template
    assert base_command.tools.cookiecutter.mock_calls == [
        mock.call(
            str(tmp_path / ".cookiecutters/template"),
            no_input=True,
            output_dir=str(tmp_path / "output"),
            checkout="v0.4.5",
            extra_context={
                "template_source": "https://example.com/template",
                "template_branch": "v0.4.5",
                "briefcase_version": str(Version(briefcase.__version__)),
                **extra_context,
            },
            default_config={
                "replay_dir": str(tmp_path / "data_path/templates/.replay")
            },
        ),
        mock.call(
            str(tmp_path / ".cookiecutters/template"),
            no_input=True,
            output_dir=str(tmp_path / "output"),
            checkout="main",
            extra_context={
                "template_source": "https://example.com/template",
                "template_branch": "main",
                "briefcase_version": str(Version(briefcase.__version__)),
                **extra_context,
            },
            default_config={
                "replay_dir": str(tmp_path / "data_path/templates/.replay")
            },
        ),
    ]

    # The context wasn't modified by generating the template
    assert extra_context == {"extra1": 37, "extra2": 42}

    # The cache patch is returned
    assert template_path == tmp_path / ".cookiecutters/template"


def test_invalid_version_branch_non_dev(monkeypatch, base_command, tmp_path):
    """If we're not in dev, and the version branch doesn't exist, an error is
    raised."""
    monkeypatch.setattr(briefcase, "__version__", "0.4.5")

    # Mock a cookiecutter failure due to a bad template
    base_command.tools.cookiecutter.side_effect = (
        cookiecutter_exceptions.RepositoryCloneFailed
    )

    extra_context = {"extra1": 37, "extra2": 42}
    with pytest.raises(InvalidTemplateBranch):
        base_command.generate_template(
            template="https://example.com/template",
            branch=None,
            output_path=tmp_path / "output",
            extra_context=extra_context,
            template_hash="deadbeef",
        )

    # An attempt was made to update the template cache
    base_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/template",
        branch="v0.4.5",
        template_hash="deadbeef",
    )
    # An attempt was made to run the cookiecutter
    base_command.tools.cookiecutter.assert_called_once_with(
        str(tmp_path / ".cookiecutters/template"),
        no_input=True,
        output_dir=str(tmp_path / "output"),
        checkout="v0.4.5",
        extra_context={
            "template_source": "https://example.com/template",
            "template_branch": "v0.4.5",
            "briefcase_version": str(Version(briefcase.__version__)),
            **extra_context,
        },
        default_config={"replay_dir": str(tmp_path / "data_path/templates/.replay")},
    )


def test_offline(base_command, tmp_path):
    """If the machine is offline, a NetworkError is raised."""
    # Mock a cookiecutter failure due to a bad template
    base_command.tools.cookiecutter.side_effect = subprocess.CalledProcessError(
        cmd="cookiecutter", returncode=1
    )

    extra_context = {"extra1": 37, "extra2": 42}
    with pytest.raises(NetworkFailure):
        base_command.generate_template(
            template="https://example.com/template",
            branch="special-branch",
            output_path=tmp_path / "output",
            extra_context=extra_context,
            template_hash="deadbeef",
        )

    # An attempt was made to update the template cache
    base_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/template",
        branch="special-branch",
        template_hash="deadbeef",
    )
    # An attempt was made to run the cookiecutter
    base_command.tools.cookiecutter.assert_called_once_with(
        str(tmp_path / ".cookiecutters/template"),
        no_input=True,
        output_dir=str(tmp_path / "output"),
        checkout="special-branch",
        extra_context={
            "template_source": "https://example.com/template",
            "template_branch": "special-branch",
            "briefcase_version": str(Version(briefcase.__version__)),
            **extra_context,
        },
        default_config={"replay_dir": str(tmp_path / "data_path/templates/.replay")},
    )


def test_invalid_repo(base_command, tmp_path):
    """If the named repository isn't a cookiecutter repository,
    RepositoryNotFound is raised."""
    # Mock a cookiecutter failure due to a bad template
    base_command.tools.cookiecutter.side_effect = (
        cookiecutter_exceptions.RepositoryNotFound
    )

    extra_context = {"extra1": 37, "extra2": 42}
    with pytest.raises(InvalidTemplateRepository):
        base_command.generate_template(
            template="https://example.com/template",
            branch="special-branch",
            output_path=tmp_path / "output",
            extra_context=extra_context,
            template_hash="deadbeef",
        )

    # An attempt was made to update the template cache
    base_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/template",
        branch="special-branch",
        template_hash="deadbeef",
    )
    # An attempt was made to run the cookiecutter
    base_command.tools.cookiecutter.assert_called_once_with(
        str(tmp_path / ".cookiecutters/template"),
        no_input=True,
        output_dir=str(tmp_path / "output"),
        checkout="special-branch",
        extra_context={
            "template_source": "https://example.com/template",
            "template_branch": "special-branch",
            "briefcase_version": str(Version(briefcase.__version__)),
            **extra_context,
        },
        default_config={"replay_dir": str(tmp_path / "data_path/templates/.replay")},
    )


def test_undefined_context_variable(base_command, tmp_path):
    """If the template requires a variable that isn't in the context, an error
    is raised."""
    # Mock a cookiecutter failure due to a bad template
    base_command.tools.cookiecutter.side_effect = (
        cookiecutter_exceptions.UndefinedVariableInTemplate(
            message="Missing variable", error="missing", context={}
        )
    )

    extra_context = {"extra1": 37, "extra2": 42}
    with pytest.raises(BriefcaseConfigError):
        base_command.generate_template(
            template="https://example.com/template",
            branch="special-branch",
            output_path=tmp_path / "output",
            extra_context=extra_context,
            template_hash="deadbeef",
        )

    # An attempt was made to update the template cache
    base_command.update_cookiecutter_cache.assert_called_once_with(
        template="https://example.com/template",
        branch="special-branch",
        template_hash="deadbeef",
    )
    # An attempt was made to run the cookiecutter
    base_command.tools.cookiecutter.assert_called_once_with(
        str(tmp_path / ".cookiecutters/template"),
        no_input=True,
        output_dir=str(tmp_path / "output"),
        checkout="special-branch",
        extra_context={
            "template_source": "https://example.com/template",
            "template_branch": "special-branch",
            "briefcase_version": str(Version(briefcase.__version__)),
            **extra_context,
        },
        default_config={"replay_dir": str(tmp_path / "data_path/templates/.replay")},
    )
