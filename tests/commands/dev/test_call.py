import pytest

from briefcase.commands import DevCommand
from briefcase.commands.base import full_options
from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError


class DummyDevCommand(DevCommand):
    """A dummy Dev command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    # Platform and format contain upper case to test case normalization
    platform = "Tester"
    output_format = "Dummy"
    description = "Dummy dev command"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("logger", Log())
        kwargs.setdefault("console", Console())
        super().__init__(*args, apps={}, **kwargs)

        self.actions = []
        self.env = dict(a=1, b=2, c=3)

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

    def install_dev_requirements(self, app, **kwargs):
        self.actions.append(("dev_requirements", app.app_name, kwargs))

    def get_environment(self, app, test_mode):
        return self.env

    def run_dev_app(self, app, env, **kwargs):
        self.actions.append(("run_dev", app.app_name, kwargs, env))
        return full_options({"run_dev_state": app.app_name, "env": env}, kwargs)


@pytest.fixture
def dev_command(tmp_path):
    return DummyDevCommand(base_path=tmp_path)


def test_no_args_one_app(dev_command, first_app):
    """If there is one app, dev starts that app by default."""
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options = dev_command.parse_options([])

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
        # Run the first app devly
        ("run_dev", "first", {"test_mode": False, "passthrough": []}, dev_command.env),
    ]


def test_no_args_two_apps(dev_command, first_app, second_app):
    """If there are two apps and no explicit app provided, an error is raised."""
    # Add two apps
    dev_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options = dev_command.parse_options([])

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
    options = dev_command.parse_options(["-a", "first"])

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
        # Run the first app devly
        ("run_dev", "first", {"test_mode": False, "passthrough": []}, dev_command.env),
    ]


def test_with_arg_two_apps(dev_command, first_app, second_app):
    """If there are multiple apps, the --app argument starts app nominated."""
    # Add two apps
    dev_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure a --app command line option
    options = dev_command.parse_options(["--app", "second"])

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
        # Run the second app devly
        ("run_dev", "second", {"test_mode": False, "passthrough": []}, dev_command.env),
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
    options = dev_command.parse_options(["--app", "does-not-exist"])

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
    options = dev_command.parse_options(["-r"])

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
        # An update was requested
        ("dev_requirements", "first", {}),
        # Then, it will be started
        ("run_dev", "first", {"test_mode": False, "passthrough": []}, dev_command.env),
    ]


def test_run_uninstalled(dev_command, first_app_uninstalled):
    """The dev command will install first if the app hasn't been installed."""
    # Add a single app
    dev_command.apps = {
        "first": first_app_uninstalled,
    }

    # Configure no command line options
    options = dev_command.parse_options([])

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
        # The app will be installed
        ("dev_requirements", "first", {}),
        # Then, it will be started
        ("run_dev", "first", {"test_mode": False, "passthrough": []}, dev_command.env),
    ]


def test_update_uninstalled(dev_command, first_app_uninstalled):
    """A request to update requirements is redundant if the app hasn't been
    installed."""
    # Add a single app
    dev_command.apps = {
        "first": first_app_uninstalled,
    }

    # Configure a requirements update
    options = dev_command.parse_options(["-r"])

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
        # An update was requested
        ("dev_requirements", "first", {}),
        # Then, it will be started
        ("run_dev", "first", {"test_mode": False, "passthrough": []}, dev_command.env),
    ]


def test_no_run(dev_command, first_app_uninstalled):
    """Install requirements without running the app."""
    # Add a single app
    dev_command.apps = {
        "first": first_app_uninstalled,
    }

    # Configure an update without run
    options = dev_command.parse_options(["--no-run"])

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
        # Only update requirements without running the app
        ("dev_requirements", "first", {}),
    ]


def test_run_test(dev_command, first_app):
    """The test suite can be run in development mode."""
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }

    # Configure the test option
    options = dev_command.parse_options(["--test"])

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
        # Then, it will be started
        ("run_dev", "first", {"test_mode": True, "passthrough": []}, dev_command.env),
    ]


def test_run_test_uninstalled(dev_command, first_app_uninstalled):
    """The test suite can be run in development mode."""
    # Add a single app
    dev_command.apps = {
        "first": first_app_uninstalled,
    }

    # Configure the test option
    options = dev_command.parse_options(["--test"])

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
        # Development requirements will be installed
        ("dev_requirements", "first", {}),
        # Then, it will be started
        ("run_dev", "first", {"test_mode": True, "passthrough": []}, dev_command.env),
    ]
