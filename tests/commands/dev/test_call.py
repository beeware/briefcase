import pytest

from briefcase.commands import DevCommand
from briefcase.commands.base import full_kwargs
from briefcase.exceptions import BriefcaseCommandError


class DummyDevCommand(DevCommand):
    """
    A dummy Dev command that doesn't actually do anything.
    It only serves to track which actions would be performend.
    """

    platform = "tester"
    output_format = "dummy"
    description = "Dummy dev command"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, apps=[], **kwargs)

        self.actions = []
        self.env = dict(a=1, b=2, c=3)

    def install_dev_dependencies(self, app, **kwargs):
        self.actions.append(("dev_dependencies", app.app_name, kwargs))

    def get_environment(self, app):
        return self.env

    def run_dev_app(self, app, env, **kwargs):
        self.actions.append(("run_dev", app.app_name, kwargs, env))
        return full_kwargs({"run_dev_state": app.app_name, "env": env}, kwargs)


@pytest.fixture
def dev_command(tmp_path):
    return DummyDevCommand(base_path=tmp_path)


def test_no_git(dev_command, first_app):
    "If Git is not installed, an error is raised"
    # Mock a non-existent git
    dev_command.git = None

    # The command will fail tool verification.
    with pytest.raises(
        BriefcaseCommandError, match=r"Briefcase requires git, but it is not installed"
    ):
        dev_command()

    # No apps will be launched
    assert dev_command.actions == []


def test_no_args_one_app(dev_command, first_app):
    "If there is one app, dev starts that app by default"
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
        # Run the first app devly
        ("run_dev", "first", {"verbosity": 1}, dev_command.env),
    ]


def test_no_args_two_apps(dev_command, first_app, second_app):
    "If there are one app, dev starts that app by default"
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

    # No apps will be launched
    assert dev_command.actions == []


def test_with_arg_one_app(dev_command, first_app):
    "If there is one app, and a -a argument, dev starts that app"
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
        # Run the first app devly
        ("run_dev", "first", {"verbosity": 1}, dev_command.env),
    ]


def test_with_arg_two_apps(dev_command, first_app, second_app):
    "If there are multiple apps, the --app argument starts app nominated"
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
        # Run the second app devly
        ("run_dev", "second", {"verbosity": 1}, dev_command.env),
    ]


def test_bad_app_reference(dev_command, first_app, second_app):
    "If the command line argument refers to an app that doesn't exist, raise an error"
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

    # No apps will be launched
    assert dev_command.actions == []


def test_update_dependencies(dev_command, first_app):
    "The dev command can request that the app is updated first"
    # Add a single app
    dev_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options = dev_command.parse_options(["-d"])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # An update was requested
        ("dev_dependencies", "first", {"verbosity": 1}),
        # Then, it will be started
        ("run_dev", "first", {"verbosity": 1}, dev_command.env),
    ]


def test_run_uninstalled(dev_command, first_app_uninstalled):
    "The dev command will install first if the app hasn't been installed"
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
        # The app will be installed
        ("dev_dependencies", "first", {"verbosity": 1}),
        # Then, it will be started
        ("run_dev", "first", {"verbosity": 1}, dev_command.env),
    ]


def test_update_uninstalled(dev_command, first_app_uninstalled):
    "A request to update dependencies is redundant if the app hasn't been installed"
    # Add a single app
    dev_command.apps = {
        "first": first_app_uninstalled,
    }

    # Configure no command line options
    options = dev_command.parse_options(["-d"])

    # Run the run command
    dev_command(**options)

    # The right sequence of things will be done
    assert dev_command.actions == [
        # An update was requested
        ("dev_dependencies", "first", {"verbosity": 1}),
        # Then, it will be started
        ("run_dev", "first", {"verbosity": 1}, dev_command.env),
    ]
