from unittest import mock

import pytest

from briefcase.commands import DevCommand
from briefcase.commands.base import full_options
from briefcase.exceptions import BriefcaseCommandError, RequirementsInstallError
from briefcase.integrations.virtual_environment import VirtualEnvironment


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

        # Mock the virtual environment manager
        self.tools.virtual_environment = mock.MagicMock()
        self.tools.virtual_environment.__getitem__ = mock.MagicMock(
            side_effect=self.virtual_environment_class
        )

        # Track which venvs exist for this command instance
        self.venvs = {}

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

    def virtual_environment_class(self, env_manager="venv"):
        # An environment manager that returns mock virtual environments,
        # tracking how they were created.
        def MockVirtualEnvironmentManager(name, app, tools, base_path, platform, arch):
            venv = mock.MagicMock(spec=VirtualEnvironment)
            venv.name = name

            # Allow the venvs dictionary to be primed with a boolean value
            # that indicates if the environment already exists. Any other
            # value is an error as we shouldn't be creating the environment
            # twice.
            existing = self.venvs.get(app.app_name, False)
            if not isinstance(existing, bool):
                pytest.fail(f"Dev environment for {app.app_name} already exists")

            def mock_prepare(recreate):
                return recreate or not existing

            venv.prepare.side_effect = mock_prepare

            # Track the action creating the environment, and cache the venv.
            self.actions.append(
                ("virtual-environment", env_manager, app.app_name, venv),
            )
            self.venvs[app.app_name] = venv
            return venv

        return MockVirtualEnvironmentManager

    def install_dev_requirements(self, app, venv, **kwargs):
        self.actions.append(("dev_requirements", app.app_name, venv))

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
    dev_command.venvs["first"] = True

    # Configure no command line options
    options, _ = dev_command.parse_options([])

    # Run the run command
    dev_command(**options)

    # A representation of the venv was generated
    first_venv = dev_command.venvs["first"]
    first_venv.prepare.assert_called_once_with(recreate=False)

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
        # Virtual environment was generated
        ("virtual-environment", "venv", "first", first_venv),
        # Run the first app devly
        (
            "run_dev",
            "first",
            False,
            first_venv,
            [],
            dev_command.env,
        ),
    ]


def test_no_args_two_apps(dev_command, first_app, second_app, monkeypatch):
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

    # A representation of the venv was generated
    second_venv = dev_command.venvs["second"]
    second_venv.prepare.assert_called_once_with(recreate=False)

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
        # Virtual environment was generated
        ("virtual-environment", "venv", "second", second_venv),
        # Requirements are installed into the venv
        ("dev_requirements", "second", second_venv),
        # Run the first app devly
        (
            "run_dev",
            "second",
            False,
            second_venv,
            [],
            dev_command.env,
        ),
    ]


def test_no_args_two_apps_non_interactive(dev_command, first_app, second_app):
    """If there are two apps and --no-input is provided, an error is raised."""
    # Add two apps
    dev_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Simulate --no-input on the command line
    options, _ = dev_command.parse_options(["--no-input"])

    # In non-interactive mode, invoking the run command raises an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Project specifies more than one application",
    ):
        dev_command(**options)

    # Finalization will not occur
    assert dev_command.actions == []


def test_with_arg_one_app(dev_command, first_app):
    """If there is one app, and a -a argument, dev starts that app."""
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }

    # Simulate that the venv already exists (installed app)
    dev_command.venvs["first"] = True

    # Configure a -a command line option
    options, _ = dev_command.parse_options(["-a", "first"])

    # Run the run command
    dev_command(**options)

    # A representation of the venv was generated
    first_venv = dev_command.venvs["first"]
    first_venv.prepare.assert_called_once_with(recreate=False)

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
        # Virtual environment was generated
        ("virtual-environment", "venv", "first", first_venv),
        # Run the first app devly
        (
            "run_dev",
            "first",
            False,
            first_venv,
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
    EXISTING_ENV = object()
    dev_command.venvs["first"] = EXISTING_ENV
    dev_command.venvs["second"] = True

    # Configure a --app command line option
    options, _ = dev_command.parse_options(["--app", "second"])

    # Run the run command
    dev_command(**options)

    # The state of the first venv hasn't changed.
    assert dev_command.venvs["first"] is EXISTING_ENV

    # A representation for the second environment was generated
    second_venv = dev_command.venvs["second"]
    second_venv.prepare.assert_called_once_with(recreate=False)

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
        # Virtual environment was generated
        ("virtual-environment", "venv", "second", second_venv),
        # Run the second app devly
        (
            "run_dev",
            "second",
            False,
            second_venv,
            [],
            dev_command.env,
        ),
    ]


def test_create_venv(dev_command, first_app):
    """If no venv exists, it is created before starting."""
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options, _ = dev_command.parse_options([])

    # Run the run command
    dev_command(**options)

    # A representation of the venv was generated
    first_venv = dev_command.venvs["first"]
    first_venv.prepare.assert_called_once_with(recreate=False)

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
        # Virtual environment was generated
        ("virtual-environment", "venv", "first", first_venv),
        # Requirements are installed into the new venv
        ("dev_requirements", "first", first_venv),
        # Run the first app devly
        (
            "run_dev",
            "first",
            False,
            first_venv,
            [],
            dev_command.env,
        ),
    ]

    # No clean calls were made.
    first_venv.clean.assert_not_called()


def test_create_venv_requirements_failure(dev_command, first_app):
    """If requirements can't be installed, the venv is cleaned up."""
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }

    # Mock a failure in the installation of development requirements
    dev_command.install_dev_requirements = mock.MagicMock(
        side_effect=RequirementsInstallError()
    )

    # Configure no command line options
    options, _ = dev_command.parse_options([])

    # Run the run command; it will raise an error
    with pytest.raises(
        RequirementsInstallError,
        match=r"Unable to install requirements\.",
    ):
        dev_command(**options)

    # A representation of the venv was generated
    first_venv = dev_command.venvs["first"]
    first_venv.prepare.assert_called_once_with(recreate=False)

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
        # Virtual environment was generated
        ("virtual-environment", "venv", "first", first_venv),
        # No further actions are recorded due to the requirements failure.
    ]

    # Clean was called to destroy the failed environment
    first_venv.clean.assert_called_once_with()


def test_non_isolated(dev_command, first_app):
    """If run in non-isolated mode, a no-op venv is created on first run."""
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options, _ = dev_command.parse_options(["--no-isolation"])

    # Run the run command
    dev_command(**options)

    # A representation of the venv was generated
    first_venv = dev_command.venvs["first"]
    first_venv.prepare.assert_called_once_with(recreate=False)

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
        # Non-isolated virtual environment was generated
        ("virtual-environment", None, "first", first_venv),
        # Requirements are installed into the venv
        ("dev_requirements", "first", first_venv),
        # Run the first app devly
        (
            "run_dev",
            "first",
            False,
            first_venv,
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
    dev_command.venvs["first"] = True

    # Configure a requirements update
    options, _ = dev_command.parse_options(["-r"])

    # Run the run command
    dev_command(**options)

    # A representation of the venv was generated,
    # and the environment was explicitly re-created
    first_venv = dev_command.venvs["first"]
    first_venv.prepare.assert_called_once_with(recreate=True)

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
        # Virtual environment was generated
        ("virtual-environment", "venv", "first", first_venv),
        # Requirements were installed again
        ("dev_requirements", "first", first_venv),
        # Then, it will be started
        (
            "run_dev",
            "first",
            False,
            first_venv,
            [],
            dev_command.env,
        ),
    ]

    # A clean call will have been made internally, but that's not tracked
    # by the mock. No *additional* clean calls were made.
    first_venv.clean.assert_not_called()


def test_install_requirements_failure(dev_command, first_app):
    """If the installation of requirements fails, the dev environment is cleaned."""
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }
    # Simulate that the venv already exists (installed app)
    dev_command.venvs["first"] = True

    # Mock a failure in the installation of development requirements
    dev_command.install_dev_requirements = mock.MagicMock(
        side_effect=RequirementsInstallError()
    )

    # Configure a requirements update
    options, _ = dev_command.parse_options(["-r"])

    # Run the run command; it will raise an error
    with pytest.raises(
        RequirementsInstallError,
        match=r"Unable to install requirements\.",
    ):
        dev_command(**options)

    # A representation of the venv was generated,
    # and the environment was explicitly re-created
    first_venv = dev_command.venvs["first"]
    first_venv.prepare.assert_called_once_with(recreate=True)

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
        # Virtual environment was generated
        ("virtual-environment", "venv", "first", first_venv),
        # But installing requirements fails.
    ]

    # Clean was called as a result of the failure.
    first_venv.clean.assert_called_once_with()


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

    # A representation of the venv was generated
    first_venv = dev_command.venvs["first"]
    first_venv.prepare.assert_called_once_with(recreate=False)

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
        # Virtual environment was generated
        ("virtual-environment", "venv", "first", first_venv),
        # The app will be installed
        ("dev_requirements", "first", first_venv),
        # Then, it will be started
        (
            "run_dev",
            "first",
            False,
            first_venv,
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

    # A representation of the venv was generated,
    # and the environment was explicitly re-created
    first_venv = dev_command.venvs["first"]
    first_venv.prepare.assert_called_once_with(recreate=True)

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
        # Virtual environment was generated
        ("virtual-environment", "venv", "first", first_venv),
        # An update was requested
        ("dev_requirements", "first", first_venv),
        # Then, it will be started
        (
            "run_dev",
            "first",
            False,
            first_venv,
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

    # A representation of the venv was generated,
    # and the environment was explicitly re-created
    first_venv = dev_command.venvs["first"]
    first_venv.prepare.assert_called_once_with(recreate=True)

    assert dev_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Virtual environment was generated
        ("virtual-environment", "venv", "first", first_venv),
        # An update was requested
        ("dev_requirements", "first", first_venv),
    ]


def test_run_test(dev_command, first_app):
    """The test suite can be run in development mode."""
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }
    # Simulate that the venv already exists (installed app)
    dev_command.venvs["first"] = True

    # Configure the test option
    options, _ = dev_command.parse_options(["--test"])

    # Run the run command
    dev_command(**options)

    # A representation of the venv was generated
    first_venv = dev_command.venvs["first"]
    first_venv.prepare.assert_called_once_with(recreate=False)

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
        # Virtual environment was generated
        ("virtual-environment", "venv", "first", first_venv),
        # Then, it will be started
        (
            "run_dev",
            "first",
            True,
            first_venv,
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

    # A representation of the venv was generated
    first_venv = dev_command.venvs["first"]
    first_venv.prepare.assert_called_once_with(recreate=False)

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
        # Virtual environment was generated
        ("virtual-environment", "venv", "first", first_venv),
        # Development requirements will be installed
        ("dev_requirements", "first", first_venv),
        # Then, it will be started
        (
            "run_dev",
            "first",
            True,
            first_venv,
            [],
            dev_command.env,
        ),
    ]
