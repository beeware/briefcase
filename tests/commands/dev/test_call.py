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

        self.tools.virtual_environment.create = mock.MagicMock(
            side_effect=self.virtual_environment
        )
        # Track which venvs exist for this command instance
        self._existing_venvs = set()

    def simulate_existing_venv(self, appname, isolated=False):
        """Mark a venv as already existing (for testing installed apps)."""
        self._existing_venvs.add((appname, isolated))

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

    def virtual_environment(self, venv_path, isolated=False, recreate=False):
        # Extract the app name from the venv_path to use as a cache key.
        app_name = venv_path.parts[-2]
        self.actions.append(("virtual-environment", app_name, isolated, recreate))

        # Simulate venv.created behavior:
        # - created=True if venv doesn't exist yet (first time) OR recreate=True
        # - created=False if venv already exists and recreate=False

        venv_key = (app_name, isolated)

        if recreate:
            # Recreating - always True
            self.mock_venv_context.created = True
        elif venv_key in self._existing_venvs:
            # Venv already exists
            self.mock_venv_context.created = False
        else:
            # First time creating this venv
            self.mock_venv_context.created = True
            self._existing_venvs.add(venv_key)

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


def test_no_args_one_app(dev_command, first_app):
    """If there is one app, dev starts that app by default."""
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }
    # Simulate that the venv already exists (installed app)
    dev_command.simulate_existing_venv("first")

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
        ("virtual-environment", "first", False, False),
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
    """If there are two apps and --no-input is provided, an error is raised."""
    # Add two apps
    dev_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Simulate --no-input on the command line
    options, _ = dev_command.parse_options(["--no-input"])

    # In non-interactive mode, invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        dev_command(**options)

    # Finalization will not occur
    assert dev_command.actions == []


def test_no_args_two_apps_interactive(dev_command, first_app, second_app, monkeypatch):
    """If there are two apps and input is enabled, the user is prompted to pick one."""
    # Add two apps
    dev_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Interactive mode
    dev_command.console.input_enabled = True

    # Fake the user selecting "second"
    def fake_selection_question(**kwargs):
        return "second"

    monkeypatch.setattr(
        dev_command.console,
        "selection_question",
        fake_selection_question,
    )

    # No flags on the command line
    options, _ = dev_command.parse_options([])

    # This should follow the multi-app selection path and run without error.
    dev_command(**options)

    # The command should perform some actions in interactive mode.
    assert dev_command.actions != []


def test_with_arg_one_app(dev_command, first_app):
    """If there is one app, and a -a argument, dev starts that app."""
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }
    # Simulate that the venv already exists (installed app)
    dev_command.simulate_existing_venv("first")

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
        ("virtual-environment", "first", False, False),
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
    # Simulate that the venvs already exist (installed apps)
    dev_command.simulate_existing_venv("first")
    dev_command.simulate_existing_venv("second")

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
        ("virtual-environment", "second", False, False),
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
    # Simulate that the venv already exists (installed app)
    dev_command.simulate_existing_venv("first")

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
        # Virtual environment context is acquired with recreate=True
        ("virtual-environment", "first", False, True),
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
        ("virtual-environment", "first", False, False),
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
        # Virtual environment context is acquired with recreate=True
        ("virtual-environment", "first", False, True),
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
        # Virtual environment context is acquired with recreate=True
        ("virtual-environment", "first", False, True),
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
    # Simulate that the venv already exists (installed app)
    dev_command.simulate_existing_venv("first")

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
        ("virtual-environment", "first", False, False),
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
        ("virtual-environment", "first", False, False),
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
