from unittest import mock

from briefcase.commands import BuildCommand, CreateCommand
from briefcase.integrations.virtual_environment import VirtualEnvironment

from ...utils import TrackingHook


class HookCommandMixin:
    """A dummy platform whose commands run the tracking hook and skip verification."""

    platform = "Tester"
    output_format = "Dummy"
    description = "Dummy command"

    def _get_hooks(self):
        return {"tracking": TrackingHook}

    def binary_path(self, app):
        return self.bundle_path(app) / f"{app.app_name}.bin"

    def verify_app(self, app):
        pass


class HookCreateCommand(HookCommandMixin, CreateCommand):
    """A create command whose steps only record that the template was generated."""

    def clone_options(self, command):
        super().clone_options(command)
        # Record on the action list of the command this one was cloned from.
        self.actions = command.actions

    def generate_app_template(self, app):
        self.actions.append(("generate", app.app_name))
        self.bundle_path(app).mkdir(parents=True)

    def install_app_support_package(self, app):
        pass

    def create_app_environment(self, app, platform, arch, **kwargs):
        venv = mock.MagicMock(spec_set=VirtualEnvironment)
        venv.provides_python = False
        return venv

    def stub_binary_revision(self, app):
        raise KeyError("stub_binary_revision")

    def install_app_code(self, app):
        pass

    def install_app_requirements(self, app, venv):
        pass

    def install_app_resources(self, app):
        pass

    def cleanup_app_content(self, app):
        pass


class HookBuildCommand(HookCommandMixin, BuildCommand):
    """A build command whose build only records that it happened."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = []

    def build_app(self, app, **kwargs):
        self.actions.append(("build", app.app_name))


# The command factory looks the cloned create command up by this name in the module
# defining the running command.
create = HookCreateCommand


def test_build_creates_through_a_cloned_command(
    dummy_console,
    tmp_path,
    mock_git,
    first_app_config,
):
    """Building an app that doesn't exist runs the create hooks, then the build
    hooks."""
    build_command = HookBuildCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        apps={"first": first_app_config},
    )
    # The cloned create command verifies git; it's never used.
    build_command.tools.git = mock_git
    options, _ = build_command.parse_options([])

    build_command(**options)

    assert build_command.actions == [
        ("hook", "pre_create", "first"),
        ("generate", "first"),
        ("hook", "post_create", "first"),
        ("hook", "pre_build", "first"),
        ("build", "first"),
        ("hook", "post_build", "first"),
    ]
