import pytest

from briefcase.commands import InstallCommand
from briefcase.exceptions import BriefcaseCommandError


class DummyInstallCommand(InstallCommand):
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

    def verify_tools(self):
        super().verify_tools()
        self.actions.append(('verify',))

    def install_dev_dependencies(self, app, update, **kwargs):
        self.actions.append(("dev_dependencies", app.app_name, update, kwargs))


@pytest.fixture
def install_command(tmp_path):
    return DummyInstallCommand(base_path=tmp_path)


def test_no_args_one_app(install_command, first_app):
    "If there is one app, dev starts that app by default"
    # Add a single app
    install_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options = install_command.parse_options([])

    # Run the run command
    install_command(**options)

    # The right sequence of things will be done
    assert install_command.actions == [
        # Tools are verified
        ('verify', ),

        # Update dependencies if needed
        ('dev_dependencies', 'first', False, {}),
    ]


def test_no_args_two_apps(install_command, first_app, second_app):
    "If there are one app, dev starts that app by default"
    # Add two apps
    install_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options = install_command.parse_options([])

    # Invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        install_command(**options)

    # No apps will be launched
    assert install_command.actions == [
        # Tools are verified
        ('verify', ),
    ]


def test_with_arg_one_app(install_command, first_app):
    "If there is one app, and a -a argument, dev starts that app"
    # Add a single app
    install_command.apps = {
        "first": first_app,
    }

    # Configure a -a command line option
    options = install_command.parse_options(["-a", "first"])

    # Run the run command
    install_command(**options)

    # The right sequence of things will be done
    assert install_command.actions == [
        # Tools are verified
        ('verify', ),

        # Update dependencies if needed
        ('dev_dependencies', 'first', False, {}),
    ]


def test_with_arg_two_apps(install_command, first_app, second_app):
    "If there are multiple apps, the --app argument starts app nominated"
    # Add two apps
    install_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure a --app command line option
    options = install_command.parse_options(["--app", "second"])

    # Run the run command
    install_command(**options)

    # The right sequence of things will be done
    assert install_command.actions == [
        # Tools are verified
        ('verify', ),

        # Update dependencies if needed
        ('dev_dependencies', 'second', False, {}),
    ]


def test_bad_app_reference(install_command, first_app, second_app):
    "If the command line argument refers to an app that doesn't exist, raise an error"
    # Add two apps
    install_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure a --app command line option
    options = install_command.parse_options(["--app", "does-not-exist"])

    # Invoking the run command raises an error
    with pytest.raises(BriefcaseCommandError):
        install_command(**options)

    # No apps will be launched
    assert install_command.actions == [
        # Tools are verified
        ('verify', ),
    ]


def test_update_dependencies(install_command, first_app):
    "The dev command can request that the app is updated first"
    # Add a single app
    install_command.apps = {
        "first": first_app,
    }

    # Configure no command line options
    options = install_command.parse_options(["-d"])

    # Run the run command
    install_command(**options)

    # The right sequence of things will be done
    assert install_command.actions == [
        # Tools are verified
        ('verify', ),

        # Update dependencies if needed
        ('dev_dependencies', 'first', True, {}),
    ]


def test_run_uninstalled(install_command, first_app_uninstalled):
    "The dev command will install first if the app hasn't been installed"
    # Add a single app
    install_command.apps = {
        "first": first_app_uninstalled,
    }

    # Configure no command line options
    options = install_command.parse_options([])

    # Run the run command
    install_command(**options)

    # The right sequence of things will be done
    assert install_command.actions == [
        # Tools are verified
        ('verify', ),

        # The app will be installed
        ("dev_dependencies", "first", False, {}),
    ]


def test_update_uninstalled(install_command, first_app_uninstalled):
    "A request to update dependencies is redundant if the app hasn't been installed"
    # Add a single app
    install_command.apps = {
        "first": first_app_uninstalled,
    }

    # Configure no command line options
    options = install_command.parse_options(["-d"])

    # Run the run command
    install_command(**options)

    # The right sequence of things will be done
    assert install_command.actions == [
        # Tools are verified
        ('verify', ),

        # An update was requested
        ("dev_dependencies", "first", True, {}),
    ]
