import pytest

from briefcase.commands import BuildCommand
from briefcase.commands.base import full_options
from briefcase.config import AppConfig
from briefcase.console import Console, Log

from ...utils import create_file


class DummyBuildCommand(BuildCommand):
    """A dummy build command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    # Platform and format contain upper case to test case normalization
    platform = "Tester"
    output_format = "Dummy"
    description = "Dummy build command"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("logger", Log())
        kwargs.setdefault("console", Console())
        super().__init__(*args, apps={}, **kwargs)

        self.actions = []

    def briefcase_toml(self, app):
        # default any app to an empty `briefcase.toml`
        return self._briefcase_toml.get(app, {})

    def binary_path(self, app):
        return self.bundle_path(app) / f"{app.app_name}.dummy.bin"

    def verify_host(self):
        super().verify_host()
        self.actions.append(("verify-host",))

    def verify_tools(self):
        super().verify_tools()
        self.actions.append(("verify-tools",))

    def finalize_app_config(self, app):
        super().finalize_app_config(app=app)
        self.actions.append(("finalize-app-config", app.app_name))

    def verify_app_template(self, app):
        super().verify_app_template(app=app)
        self.actions.append(("verify-app-template", app.app_name))

    def verify_app_tools(self, app):
        super().verify_app_tools(app=app)
        self.actions.append(("verify-app-tools", app.app_name))

    def build_app(self, app, **kwargs):
        self.actions.append(("build", app.app_name, kwargs.copy()))
        # Remove arguments consumed by the underlying call to build_app()
        kwargs.pop("update", None)
        kwargs.pop("update_requirements", None)
        kwargs.pop("update_resources", None)
        kwargs.pop("update_support", None)
        kwargs.pop("no_update", None)
        kwargs.pop("test_mode", None)
        return full_options({"build_state": app.app_name}, kwargs)

    # These commands override the default behavior, simply tracking that
    # they were invoked, rather than instantiating a Create/Update command.
    # This is for testing purposes.
    def create_command(self, app, **kwargs):
        self.actions.append(("create", app.app_name, kwargs.copy()))
        # Remove arguments consumed by the underlying call to create_app()
        kwargs.pop("test_mode", None)
        return full_options({"create_state": app.app_name}, kwargs)

    def update_command(self, app, **kwargs):
        self.actions.append(("update", app.app_name, kwargs.copy()))
        # Remove arguments consumed by the underlying call to update_app()
        kwargs.pop("update_requirements", None)
        kwargs.pop("update_resources", None)
        kwargs.pop("update_support", None)
        kwargs.pop("test_mode", None)
        return full_options({"update_state": app.app_name}, kwargs)


@pytest.fixture
def build_command(tmp_path):
    return DummyBuildCommand(base_path=tmp_path / "base_path")


@pytest.fixture
def second_app_config():
    return AppConfig(
        app_name="second",
        bundle="com.example",
        version="0.0.2",
        description="The second simple app",
        sources=["src/second"],
    )


@pytest.fixture
def second_app(second_app_config, tmp_path):
    # The same fixture as second_app_config,
    # but ensures that the binary for the app exists
    create_file(
        tmp_path
        / "base_path"
        / "build"
        / "second"
        / "tester"
        / "dummy"
        / "second.bundle",
        "second.bundle",
    )
    create_file(
        tmp_path / "base_path/build/second/tester/dummy/second.bin",
        "second.bin",
    )

    return second_app_config
