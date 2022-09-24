import pytest

from briefcase.commands import BuildCommand
from briefcase.commands.base import full_options
from briefcase.config import AppConfig
from briefcase.console import Console, Log


class DummyBuildCommand(BuildCommand):
    """A dummy build command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    platform = "tester"
    output_format = "dummy"
    description = "Dummy build command"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("logger", Log())
        kwargs.setdefault("console", Console())
        super().__init__(*args, apps={}, **kwargs)

        self.actions = []

    def bundle_path(self, app):
        return self.platform_path / f"{app.app_name}.dummy"

    def binary_path(self, app):
        return self.platform_path / f"{app.app_name}.dummy.bin"

    def distribution_path(self, app, packaging_format):
        return self.platform_path / f"{app.app_name}.dummy.{packaging_format}"

    def verify_tools(self):
        super().verify_tools()
        self.actions.append(("verify",))

    def verify_app_tools(self, app):
        super().verify_app_tools(app=app)
        self.actions.append(("verify-app-tools", app.app_name))

    def build_app(self, app, **kwargs):
        self.actions.append(("build", app.app_name, kwargs))
        return full_options({"build_state": app.app_name}, kwargs)

    # These commands override the default behavior, simply tracking that
    # they were invoked, rather than instantiating a Create/Update command.
    # This is for testing purposes.
    def create_command(self, app, **kwargs):
        self.actions.append(("create", app.app_name, kwargs))
        return full_options({"create_state": app.app_name}, kwargs)

    def update_command(self, app, **kwargs):
        self.actions.append(("update", app.app_name, kwargs))
        return full_options({"update_state": app.app_name}, kwargs)


@pytest.fixture
def build_command(tmp_path):
    return DummyBuildCommand(base_path=tmp_path)


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
    (tmp_path / "tester").mkdir(parents=True, exist_ok=True)
    with (tmp_path / "tester" / "second.dummy").open("w") as f:
        f.write("second.bundle")
    with (tmp_path / "tester" / "second.dummy.bin").open("w") as f:
        f.write("second.exe")

    return second_app_config
