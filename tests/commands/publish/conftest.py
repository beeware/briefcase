import pytest

from briefcase.commands import PublishCommand
from briefcase.commands.base import full_options
from briefcase.config import AppConfig
from briefcase.console import Console, Log

from ...utils import create_file


class DummyPublishCommand(PublishCommand):
    """A dummy publish command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    # Platform and format contain upper case to test case normalization
    platform = "Tester"
    output_format = "Dummy"
    description = "Dummy publish command"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("logger", Log())
        kwargs.setdefault("console", Console())
        super().__init__(*args, apps={}, **kwargs)

        self.actions = []

    def briefcase_toml(self, app):
        # default any app to an empty `briefcase.toml`
        return self._briefcase_toml.get(app, {})

    def binary_path(self, app):
        return self.bundle_path(app) / f"{app.app_name}.bin"

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

    @property
    def publication_channels(self):
        return ["s3", "alternative"]

    @property
    def default_publication_channel(self):
        return "s3"

    def publish_app(self, app, channel, **kwargs):
        self.actions.append(("publish", app.app_name, channel, kwargs.copy()))
        return full_options({"publish_state": app.app_name}, kwargs)

    # These commands override the default behavior, simply tracking that
    # they were invoked, rather than instantiating a Create/Update/Build command.
    # This is for testing purposes.
    def create_command(self, app, **kwargs):
        self.actions.append(("create", app.app_name, kwargs.copy()))
        # Remove arguments consumed by the underlying call to create_app()
        kwargs.pop("test_mode", None)
        return full_options({"create_state": app.app_name}, kwargs)

    def update_command(self, app, **kwargs):
        self.actions.append(("update", app.app_name, kwargs.copy()))
        # Remove arguments consumed by the underlying call to update_app()
        kwargs.pop("test_mode", None)
        kwargs.pop("update_requirements", None)
        kwargs.pop("update_resources", None)
        kwargs.pop("update_support", None)
        return full_options({"update_state": app.app_name}, kwargs)

    def build_command(self, app, **kwargs):
        self.actions.append(("build", app.app_name, kwargs.copy()))
        # Remove arguments consumed by the underlying call to build_app()
        kwargs.pop("test_mode", None)
        kwargs.pop("update", None)
        return full_options({"build_state": app.app_name}, kwargs)


@pytest.fixture
def publish_command(tmp_path):
    return DummyPublishCommand(base_path=tmp_path / "base_path")


@pytest.fixture
def first_app_config():
    return AppConfig(
        app_name="first",
        bundle="com.example",
        version="0.0.1",
        description="The first simple app",
        sources=["src/first"],
    )


@pytest.fixture
def first_app_unbuilt(first_app_config, tmp_path):
    # The same fixture as first_app_config,
    # but ensures that the bundle for the app exists
    create_file(
        tmp_path
        / "base_path"
        / "build"
        / "tester"
        / "first"
        / "tester"
        / "dummy"
        / "first.bundle",
        "first.bundle",
    )

    return first_app_config


@pytest.fixture
def first_app(first_app_unbuilt, tmp_path):
    # The same fixture as first_app_config,
    # but ensures that the binary for the app exists
    create_file(
        tmp_path / "base_path/build/first/tester/dummy/first.bin",
        "first.bin",
    )

    return first_app_unbuilt


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
