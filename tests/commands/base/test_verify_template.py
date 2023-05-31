import pytest

from briefcase.exceptions import BriefcaseCommandError

from ...utils import create_file


def test_no_target_versions(base_command, my_app):
    """Verification succeeds if no target versions are declared."""
    base_command.platform_target_version = None

    create_file(base_command.bundle_path(my_app) / "briefcase.toml", content="")

    base_command.verify_app_template(my_app)


def test_platform_version_compatible(base_command, my_app):
    """Verification succeeds when template version matches platform version."""
    base_command.platform_target_version = "42.42"

    create_file(
        base_command.bundle_path(my_app) / "briefcase.toml",
        content="[briefcase]\ntarget_version = '42.42'",
    )

    base_command.verify_app_template(my_app)


@pytest.mark.parametrize("template_version", ["", "32.32", "52.52"])
def test_platform_version_incompatible(base_command, my_app, template_version):
    """Verification fails when template version doesn't match platform version."""
    base_command.platform_target_version = "42.42"

    create_file(
        base_command.bundle_path(my_app) / "briefcase.toml",
        content=f"[briefcase]\ntarget_version = '{template_version}'",
    )

    with pytest.raises(
        BriefcaseCommandError,
        match="The app template used to generate this app is not compatible with this version\nof Briefcase.",
    ):
        base_command.verify_app_template(my_app)
