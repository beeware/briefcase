from unittest import mock

import pytest

from briefcase.commands import DevCommand
from briefcase.commands.base import full_options
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.virtual_environment import VenvContext


class DummyDevCommand(DevCommand):
    """A dummy Dev command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    # Platform and format contain upper case to test case normalization
    platform = "Tester"
    output_format = "Dummy"
    description = "Dummy dev command"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, apps={}, **kwargs)

        self.actions = []
        self.env = {"a": 1, "b": 2, "c": 3}
        self.mock_venv_context = mock.MagicMock(spec=VenvContext)

    def verify_host(self):
        super().verify_host()
        self.actions.append(("verify-host",))

    def verify_tools(self):
        super().verify_tools()
        self.actions.append(("verify-tools",))

    def verify_app_template(self, app):
        super().verify_app_template(app=app)
        self.actions.append(("verify-app-template", app.app_name))

    def verify_app_tools(self, app):
        super().verify_app_tools(app=app)
        self.actions.append(("verify-app-tools", app.app_name))

    def get_venv_context(self, appname, isolated=False):
        self.actions.append(("get-venv-context", appname, isolated))
        mock_context = mock.MagicMock()
        mock_context.__enter__.return_value = self.mock_venv_context
        mock_context.__exit__.return_value = False
        return mock_context

    def install_dev_requirements(self, app, venv, **kwargs):
        self.actions.append(
            (
                "dev_requirements",
                app.app_name,
                venv,
            )
        )

    def get_environment(self, app):
        return self.env

    def run_dev_app(self, app, env, venv, passthrough, **kwargs):
        self.actions.append(
            (
                "run_dev",
                app.app_name,
                app.test_mode,
                venv,
                passthrough,
                env,
            )
        )
        return full_options({"run_dev_state": app.app_name, "env": env}, kwargs)


@pytest.fixture
def dev_command(dummy_console, tmp_path):
    return DummyDevCommand(
        console=dummy_console,
        base_path=tmp_path,
    )


@pytest.fixture(autouse=True)
def mock_virtual_environment(dev_command):
    """Mock virtual_environment to return our predictable VenvContext regardless of
    isolated parameter."""

    def mock_venv_factory(tools, console, venv_path, *, isolated=False, recreate=False):
        """Mock factory that always returns a context manager yielding our VenvContext.

        This handles both isolated=True and isolated=False cases to always return our
        predictable mock instead of NoOpEnvironment returning tools.subprocess.
        """
        mock_context = mock.MagicMock()
        mock_context.__enter__.return_value = dev_command.mock_venv_context
        mock_context.__exit__.return_value = False
        return mock_context

    with mock.patch(
        "briefcase.commands.dev.virtual_environment", side_effect=mock_venv_factory
    ):
        yield


def test_no_args_one_app(dev_command, first_app):
    """If there is one app, dev starts that app by default."""
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options, _ = dev_command.parse_options([])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Virtual environment context is acquired
        ("get-venv-context", "first", False),
        # Run the first app devly
        (
            "run_dev",
            "first",
            False,
            dev_command.mock_venv_context,
            [],
            dev_command.env,
        ),
    ]


def test_no_args_two_apps(dev_command, first_app, second_app):
    """If there are two apps and no explicit app provided, an error is raised."""
    # Add two apps
    dev_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options, _ = dev_command.parse_options([])

    # Invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        dev_command(**options)

    # Finalization will not occur.
    assert dev_command.actions == []


def test_with_arg_one_app(dev_command, first_app):
    """If there is one app, and a -a argument, dev starts that app."""
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }

    # Configure a -a command line option
    options, _ = dev_command.parse_options(["-a", "first"])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Virtual environment context is acquired
        ("get-venv-context", "first", False),
        # Run the first app devly
        (
            "run_dev",
            "first",
            False,
            dev_command.mock_venv_context,
            [],
            dev_command.env,
        ),
    ]


def test_with_arg_two_apps(dev_command, first_app, second_app):
    """If there are multiple apps, the --app argument starts app nominated."""
    # Add two apps
    dev_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure a --app command line option
    options, _ = dev_command.parse_options(["--app", "second"])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App template is verified
        ("verify-app-template", "second"),
        # App tools are verified for app
        ("verify-app-tools", "second"),
        # Virtual environment context is acquired
        ("get-venv-context", "second", False),
        # Run the second app devly
        (
            "run_dev",
            "second",
            False,
            dev_command.mock_venv_context,
            [],
            dev_command.env,
        ),
    ]


def test_bad_app_reference(dev_command, first_app, second_app):
    """If the command line argument refers to an app that doesn't exist, raise an
    error."""
    # Add two apps
    dev_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure a --app command line option
    options, _ = dev_command.parse_options(["--app", "does-not-exist"])

    # Invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        dev_command(**options)

    # Finalization will not occur.
    assert dev_command.actions == []


def test_update_requirements(dev_command, first_app):
    """The dev command can request that the app is updated first."""
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }

    # Configure a requirements update
    options, _ = dev_command.parse_options(["-r"])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Virtual environment context is acquired
        ("get-venv-context", "first", False),
        # An update was requested
        (
            "dev_requirements",
            "first",
            dev_command.mock_venv_context,
        ),
        # Then, it will be started
        (
            "run_dev",
            "first",
            False,
            dev_command.mock_venv_context,
            [],
            dev_command.env,
        ),
    ]


def test_run_uninstalled(dev_command, first_app_uninstalled):
    """The dev command will install first if the app hasn't been installed."""
    # Add a single app
    dev_command.apps = {
        "first": first_app_uninstalled,
    }

    # Configure no command line options
    options, _ = dev_command.parse_options([])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Virtual environment context is acquired
        ("get-venv-context", "first", False),
        # The app will be installed
        (
            "dev_requirements",
            "first",
            dev_command.mock_venv_context,
        ),
        # Then, it will be started
        (
            "run_dev",
            "first",
            False,
            dev_command.mock_venv_context,
            [],
            dev_command.env,
        ),
    ]


def test_update_uninstalled(dev_command, first_app_uninstalled):
    """A request to update requirements is redundant if the app hasn't been
    installed."""
    # Add a single app
    dev_command.apps = {
        "first": first_app_uninstalled,
    }

    # Configure a requirements update
    options, _ = dev_command.parse_options(["-r"])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Virtual environment context is acquired
        ("get-venv-context", "first", False),
        # An update was requested
        (
            "dev_requirements",
            "first",
            dev_command.mock_venv_context,
        ),
        # Then, it will be started
        (
            "run_dev",
            "first",
            False,
            dev_command.mock_venv_context,
            [],
            dev_command.env,
        ),
    ]


def test_no_run(dev_command, first_app_uninstalled):
    """Install requirements without running the app."""
    # Add a single app
    dev_command.apps = {
        "first": first_app_uninstalled,
    }

    # Configure an update without run
    options, _ = dev_command.parse_options(["--no-run"])

    # Run the run command
    dev_command(**options)

    assert dev_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Virtual environment context is acquired
        ("get-venv-context", "first", False),
        # An update was requested
        (
            "dev_requirements",
            "first",
            dev_command.mock_venv_context,
        ),
    ]


def test_run_test(dev_command, first_app):
    """The test suite can be run in development mode."""
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }

    # Configure the test option
    options, _ = dev_command.parse_options(["--test"])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Virtual environment context is acquired
        ("get-venv-context", "first", False),
        # Then, it will be started
        (
            "run_dev",
            "first",
            True,
            dev_command.mock_venv_context,
            [],
            dev_command.env,
        ),
    ]


def test_run_test_uninstalled(dev_command, first_app_uninstalled):
    """The test suite can be run in development mode."""
    # Add a single app
    dev_command.apps = {
        "first": first_app_uninstalled,
    }

    # Configure the test option
    options, _ = dev_command.parse_options(["--test"])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Virtual environment context is acquired
        ("get-venv-context", "first", False),
        # Development requirements will be installed
        ("dev_requirements", "first", dev_command.mock_venv_context),
        # Then, it will be started
        (
            "run_dev",
            "first",
            True,
            dev_command.mock_venv_context,
            [],
            dev_command.env,
        ),
    ]


def test_get_venv_context_isolated(dummy_console, tmp_path):
    """The base DevCommand.get_venv_context() method works with isolated=True."""
    mock_dev_command = mock.MagicMock(spec=DevCommand)
    mock_dev_command.tools = mock.MagicMock()
    mock_dev_command.console = dummy_console
    mock_dev_command.base_path = tmp_path / "base_path"

    with mock.patch("briefcase.commands.dev.virtual_environment") as mock_venv:
        result = DevCommand.get_venv_context(
            mock_dev_command, "test-app", isolated=True
        )

        expected_venv_path = tmp_path / "base_path" / ".briefcase" / "test-app" / "venv"
        mock_venv.assert_called_once_with(
            tools=mock_dev_command.tools,
            console=mock_dev_command.console,
            venv_path=expected_venv_path,
            isolated=True,
        )
        assert result == mock_venv.return_value


def test_get_venv_context_not_isolated(dummy_console, tmp_path):
    """The base DevCommand.get_venv_context() method works with isolated=False."""
    mock_dev_command = mock.MagicMock(spec=DevCommand)
    mock_dev_command.tools = mock.MagicMock()
    mock_dev_command.console = dummy_console
    mock_dev_command.base_path = tmp_path / "base_path"

    with mock.patch("briefcase.commands.dev.virtual_environment") as mock_venv:
        result = DevCommand.get_venv_context(mock_dev_command, "my-app", isolated=False)

        expected_venv_path = tmp_path / "base_path" / ".briefcase" / "my-app" / "venv"
        mock_venv.assert_called_once_with(
            tools=mock_dev_command.tools,
            console=mock_dev_command.console,
            venv_path=expected_venv_path,
            isolated=False,
        )
        assert result == mock_venv.return_value
