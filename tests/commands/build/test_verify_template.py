import pytest

from briefcase.commands.build import briefcase
from briefcase.exceptions import BriefcaseCommandError


def test_no_target_versions(build_command, first_app_config, monkeypatch):
    """Template verification succeeds if no target versions are specified."""
    build_command.oldest_compatible_briefcase = None
    build_command._briefcase_toml[first_app_config] = {}
    monkeypatch.setattr(briefcase, "__version__", "1.5.2")

    build_command(first_app_config)


def test_platform_target_without_template_target(
    build_command,
    first_app_config,
    monkeypatch,
):
    """Template verification fails if no template target exists when a platform target
    is specified."""
    build_command.oldest_compatible_briefcase = "0.1.42"
    build_command._briefcase_toml[first_app_config] = {}
    monkeypatch.setattr(briefcase, "__version__", "1.5.2")

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            "Briefcase requires that the app template explicitly declare that it is compatible\n"
            "with Briefcase 0.1.42 or later"
        ),
    ):
        build_command(first_app_config)


@pytest.mark.parametrize("template_target", ["0.0.42", "0.1.40", "0.1.41"])
def test_platform_target_with_incompatible_template_target(
    build_command,
    first_app_config,
    template_target,
    monkeypatch,
):
    """Template verification fails if template target is older than platform target."""
    build_command.oldest_compatible_briefcase = "0.1.42"
    build_command._briefcase_toml[first_app_config] = {
        "briefcase": {"target_version": template_target}
    }
    monkeypatch.setattr(briefcase, "__version__", "1.5.2")

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            "The app template used to generate this app is not compatible with this version\n"
            "of Briefcase. Briefcase requires a template that is compatible with version 0.1.42"
        ),
    ):
        build_command(first_app_config)


@pytest.mark.parametrize("template_target", ["0.1.42", "0.1.43", "1.2.0"])
def test_platform_target_with_compatible_template_target(
    build_command,
    first_app_config,
    template_target,
    monkeypatch,
):
    """Template verification succeeds if template target is newer than platform
    target."""
    build_command.oldest_compatible_briefcase = "0.1.42"
    build_command._briefcase_toml[first_app_config] = {
        "briefcase": {"target_version": template_target}
    }
    monkeypatch.setattr(briefcase, "__version__", "1.5.2")

    build_command(first_app_config)


@pytest.mark.parametrize("template_target", ["0.1.5", "1.5.0", "1.5.1"])
def test_current_version_with_incompatible_template_target(
    build_command,
    first_app_config,
    template_target,
    monkeypatch,
):
    """Template verification succeeds if template target is older than current
    version."""
    build_command._briefcase_toml[first_app_config] = {
        "briefcase": {"target_version": template_target}
    }
    monkeypatch.setattr(briefcase, "__version__", "1.5.2")

    build_command(first_app_config)


@pytest.mark.parametrize("template_target", ["1.5.3", "1.5.4", "2.0.0"])
def test_current_version_with_compatible_template_target(
    build_command,
    first_app_config,
    template_target,
    monkeypatch,
):
    """Template verification fails if template target is newer than current version."""
    build_command._briefcase_toml[first_app_config] = {
        "briefcase": {"target_version": template_target}
    }
    monkeypatch.setattr(briefcase, "__version__", "1.5.2")

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            "The app template used to generate this app is not compatible with this version\n"
            "of Briefcase. Briefcase requires a template that is compatible with version 1.5.2"
        ),
    ):
        build_command(first_app_config)
