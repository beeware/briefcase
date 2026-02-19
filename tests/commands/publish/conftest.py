import pytest

from briefcase.commands import PublishCommand
from briefcase.commands.base import full_options
from briefcase.config import AppConfig
from briefcase.publication_channels.base import BasePublicationChannel

from ...utils import create_file


class DummyPublicationChannel(BasePublicationChannel):
    """A publication channel that records calls on the command's action list."""

    @property
    def name(self):
        return self._name

    def publish_app(self, app, command, **options):
        command.actions.append(("publish", app.app_name, self._name, options.copy()))
        return {"publish_state": app.app_name}


def _make_channel_class(channel_name):
    """Create a DummyPublicationChannel subclass with the given name."""
    return type(
        f"Dummy_{channel_name}",
        (DummyPublicationChannel,),
        {"_name": channel_name},
    )


class DummyPublishCommand(PublishCommand):
    """A dummy publish command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    # Platform and format contain upper case to test case normalization
    platform = "Tester"
    output_format = "Dummy"
    description = "Dummy publish command"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, apps={}, **kwargs)

        self.actions = []

    def briefcase_toml(self, app):
        # default any app to an empty `briefcase.toml`
        return self._briefcase_toml.get(app, {})

    def binary_path(self, app):
        return self.bundle_path(app) / f"{app.app_name}.bin"

    def distribution_path(self, app):
        return self.dist_path / f"{app.app_name}.pkg"

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

    def _get_channels(self):
        return {
            "s3": _make_channel_class("s3"),
            "alternative": _make_channel_class("alternative"),
        }

    # These commands override the default behavior, simply tracking that
    # they were invoked, rather than instantiating a Create/Update/Build/Package command.
    # This is for testing purposes.
    def package_command(self, app, **kwargs):
        self.actions.append(("package", app.app_name, kwargs.copy()))
        # Remove arguments consumed by the underlying call to package_app()
        kwargs.pop("update", None)
        kwargs.pop("packaging_format", None)
        return full_options({"package_state": app.app_name}, kwargs)

    def create_command(self, app, **kwargs):
        self.actions.append(("create", app.app_name, kwargs.copy()))
        # Remove arguments consumed by the underlying call to create_app()
        return full_options({"create_state": app.app_name}, kwargs)

    def update_command(self, app, **kwargs):
        self.actions.append(("update", app.app_name, kwargs.copy()))
        # Remove arguments consumed by the underlying call to update_app()
        kwargs.pop("update_requirements", None)
        kwargs.pop("update_resources", None)
        kwargs.pop("update_support", None)
        return full_options({"update_state": app.app_name}, kwargs)

    def build_command(self, app, **kwargs):
        self.actions.append(("build", app.app_name, kwargs.copy()))
        # Remove arguments consumed by the underlying call to build_app()
        kwargs.pop("update", None)
        return full_options({"build_state": app.app_name}, kwargs)


@pytest.fixture
def publish_command(dummy_console, tmp_path):
    return DummyPublishCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
    )


@pytest.fixture
def first_app_config():
    return AppConfig(
        app_name="first",
        bundle="com.example",
        version="0.0.1",
        description="The first simple app",
        sources=["src/first"],
        license={"file": "LICENSE"},
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
def first_app_unpackaged(first_app_unbuilt, tmp_path):
    # The same fixture as first_app_unbuilt,
    # but ensures that the binary exists (no distribution artefact)
    create_file(
        tmp_path / "base_path/build/first/tester/dummy/first.bin",
        "first.bin",
    )

    return first_app_unbuilt


@pytest.fixture
def first_app(first_app_unpackaged, tmp_path):
    # The same fixture as first_app_unpackaged,
    # but ensures that the distribution artefact also exists
    create_file(
        tmp_path / "base_path/dist/first.pkg",
        "first.pkg",
    )

    return first_app_unpackaged


@pytest.fixture
def second_app_config():
    return AppConfig(
        app_name="second",
        bundle="com.example",
        version="0.0.2",
        description="The second simple app",
        sources=["src/second"],
        license={"file": "LICENSE"},
    )


@pytest.fixture
def second_app(second_app_config, tmp_path):
    # The same fixture as second_app_config,
    # but ensures that the binary and distribution artefact exist
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
    create_file(
        tmp_path / "base_path/dist/second.pkg",
        "second.pkg",
    )

    return second_app_config
