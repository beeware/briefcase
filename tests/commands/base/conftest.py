import pytest

from briefcase.commands.base import BaseCommand
from briefcase.config import AppConfig
from briefcase.console import Console, Log


class DummyCommand(BaseCommand):
    """A dummy command to test the BaseCommand interface."""

    command = ("dummy",)
    # Platform and format contain upper case to test case normalization
    platform = "Tester"
    output_format = "Dummy"
    description = "Dummy base command"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("logger", Log())
        kwargs.setdefault("console", Console())
        super().__init__(*args, **kwargs)

        self.actions = []

    def add_options(self, parser):
        # Provide some extra arguments:
        # * some optional arguments
        parser.add_argument("-x", "--extra")
        parser.add_argument("-m", "--mystery")
        # * a required argument
        parser.add_argument("-r", "--required", required=True)

    def binary_path(self, app):
        raise NotImplementedError()

    def verify_host(self):
        super().verify_host()
        self.actions.append(("verify-host",))

    def verify_tools(self):
        super().verify_tools()
        self.actions.append(("verify-tools",))

    def finalize_app_config(self, app):
        super().finalize_app_config(app=app)
        self.actions.append(("finalize-app-config", app.app_name))


@pytest.fixture
def base_command(tmp_path):
    command = DummyCommand(base_path=tmp_path / "base_path")
    command.parse_options(["-r", "default"])
    return command


# Define some stub command classes
# These will be used to test the command accessor
class DummyCreateCommand(DummyCommand):
    description = "Test Create"


class DummyUpdateCommand(DummyCommand):
    description = "Test Update"


class DummyBuildCommand(DummyCommand):
    description = "Test Build"


class DummyRunCommand(DummyCommand):
    description = "Test Run"


class DummyPackageCommand(DummyCommand):
    description = "Test Package"


class DummyPublishCommand(DummyCommand):
    description = "Test Publish"


# Register the commands with the module
create = DummyCreateCommand
update = DummyUpdateCommand
build = DummyBuildCommand
run = DummyRunCommand
package = DummyPackageCommand
publish = DummyPublishCommand


class OtherDummyCommand(BaseCommand):
    command = ("other",)
    platform = "tester"
    output_format = "dumdum"
    description = "Another dummy command"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def binary_path(self, app):
        raise NotImplementedError()


@pytest.fixture
def other_command(tmp_path):
    return OtherDummyCommand(base_path=tmp_path, logger=Log(), console=Console())


@pytest.fixture
def my_app():
    return AppConfig(
        app_name="my-app",
        formal_name="My App",
        bundle="com.example",
        version="1.2.3",
        description="This is a simple app",
        sources=["src/my_app"],
    )
