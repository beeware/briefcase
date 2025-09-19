from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError, UnsupportedCommandError
from briefcase.platforms.web.static import StaticWebDevCommand


class DummyStaticWebDevCommand(StaticWebDevCommand):
    """A dummy static web dev command that doesn't actually do anything.

    It only serves to track which actions would be performed.
    """

    platform = "Tester"
    output_format = "Dummy"
    description = "Dummy static web dev command"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, apps={}, **kwargs)
        self.actions = []

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

    def finalize(self, app, test_mode=False):
        super().finalize(app=app, test_mode=test_mode)
        self.actions.append(("finalize", app.app_name))

    def install_dev_requirements(self, app, venv, **kwargs):
        _ = venv, kwargs
        self.actions.append(("install-dev-requirements", app.app_name))


@pytest.fixture
def dev_command(dummy_console, tmp_path):
    return DummyStaticWebDevCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_no_args_one_app(dev_command, first_app_config, tmp_path):
    """If there is one app, dev starts that app by default and hits
    UnsupportedCommandError."""
    (tmp_path / "base_path/src").mkdir(parents=True, exist_ok=True)

    dev_command.apps = {
        "first-app": first_app_config,
    }

    options, _ = dev_command.parse_options([])

    with pytest.raises(UnsupportedCommandError):
        dev_command(**options)

    assert dev_command.actions == [
        ("verify-host",),
        ("verify-tools",),
        ("finalize", "first-app"),
        ("verify-app-template", "first-app"),
        ("verify-app-tools", "first-app"),
        ("install-dev-requirements", "first-app"),
    ]


def test_run_dev_app_raises_unsupported_command_error(dev_command, first_app_config):
    """Test that run_dev_app raises UnsupportedCommandError for web platform."""
    with pytest.raises(UnsupportedCommandError) as excinfo:
        dev_command.run_dev_app(first_app_config)

    assert excinfo.value.platform == "web"
    assert excinfo.value.output_format == "static"
    assert excinfo.value.command == "dev"


def test_bad_app_reference(dev_command, first_app_config):
    """If the command line argument refers to an app that doesn't exist, raise an
    error."""

    mock_second_app = mock.MagicMock()
    mock_second_app.app_name = "second"

    dev_command.apps = {
        "first-app": first_app_config,
        "second": mock_second_app,
    }

    with pytest.raises(BriefcaseCommandError) as exc:
        dev_command(appname="non_existent_app", run_app=True, update_requirements=False)

    assert "doesn't define an application named 'non_existent_app'" in str(exc.value)


def test_no_args_two_apps(dev_command, first_app_config):
    """If there are two apps and no explicit app provided, an error is raised."""
    from briefcase.exceptions import BriefcaseCommandError

    mock_second_app = mock.MagicMock()
    mock_second_app.app_name = "second"

    dev_command.apps = {
        "first-app": first_app_config,
        "second": mock_second_app,
    }

    with pytest.raises(BriefcaseCommandError) as exc:
        dev_command(appname=None, run_app=True, update_requirements=False)

    assert "specifies more than one application" in str(exc.value)
