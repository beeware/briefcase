import pytest

from briefcase.exceptions import BriefcaseCommandError

from ...utils import create_file


def test_no_target_epochs(base_command, my_app):
    """Verification succeeds if no target epochs are declared."""
    base_command.platform_target_epoch = None

    create_file(base_command.bundle_path(my_app) / "briefcase.toml", content="")

    base_command.verify_app_template(my_app)


def test_platform_epoch_compatible(base_command, my_app):
    """Verification succeeds when template epoch matches platform epoch."""
    base_command.platform_target_epoch = "42.42"

    create_file(
        base_command.bundle_path(my_app) / "briefcase.toml",
        content="[briefcase]\ntarget_epoch = '42.42'",
    )

    base_command.verify_app_template(my_app)


@pytest.mark.parametrize("template_epoch", ["", "32.32", "52.52"])
def test_platform_epoch_incompatible(base_command, my_app, template_epoch):
    """Verification fails when template epoch doesn't match platform epoch."""
    base_command.platform_target_epoch = "42.42"

    create_file(
        base_command.bundle_path(my_app) / "briefcase.toml",
        content=f"[briefcase]\ntarget_epoch = '{template_epoch}'",
    )

    with pytest.raises(
        BriefcaseCommandError,
        match="The app template used to generate this app is not compatible with this version\nof Briefcase.",
    ):
        base_command.verify_app_template(my_app)
