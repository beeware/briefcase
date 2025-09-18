from unittest import mock

import pytest

from briefcase.commands.base import full_options
from briefcase.integrations.virtual_environment import VenvContext
from briefcase.platforms.web.static import StaticWebDevCommand


class DummyStaticWebDevCommand(StaticWebDevCommand):
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
    return DummyStaticWebDevCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
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
        ),
    ]


# @pytest.fixture
# def dev_command(dummy_console, tmp_path):
#     return StaticWebDevCommand(
#         console=dummy_console,
#         base_path=tmp_path / "base_path",
#         data_path=tmp_path / "briefcase",
#     )


# def test_web_dev_creates_venv_single_app_directory(
#     monkeypatch, tmp_path, dev_command, first_app_built
# ):
#     """StaticWebDevCommand creates a venv when directory has a single app, then raises
#     UnsupportedCommandError."""
#     venv_path = (
#         tmp_path / "base_path" / ".briefcase" / first_app_built.app_name / "venv"
#     )
#     run_log = {}

#     # Fake subprocess.run to simulate venv creation
#     def fake_run(self, args, check=True, **kwargs):
#         run_log["called"] = True
#         venv_path.mkdir(parents=True, exist_ok=True)
#         (venv_path / "pyvenv.cfg").touch()
#         (venv_path / ("Scripts" if os.name == "nt" else "bin")).mkdir(exist_ok=True)

#     monkeypatch.setattr(ve.VenvContext, "run", fake_run, raising=True)

#     dev_command.apps = {"first-app": first_app_built}

#     with pytest.raises(UnsupportedCommandError):
#         dev_command(appname="first-app", run_app=True, update_requirements=False)

#     assert run_log.get("called") is True
#     assert (venv_path / "pyvenv.cfg").exists()


# def test_web_dev_creates_venv_multi_app_directory(
#     monkeypatch, tmp_path, dev_command, first_app_built
# ):
#     """StaticWebDevCommand creates a venv when directory has multiple apps, then raises
#     UnsupportedCommandError."""
#     venv_path = (
#         tmp_path / "base_path" / ".briefcase" / first_app_built.app_name / "venv"
#     )
#     run_log = {}

#     # Fake subprocess.run to simulate venv creation
#     def fake_run(self, args, check=True, **kwargs):
#         run_log["called"] = True
#         venv_path.mkdir(parents=True, exist_ok=True)
#         (venv_path / "pyvenv.cfg").touch()
#         (venv_path / ("Scripts" if os.name == "nt" else "bin")).mkdir(exist_ok=True)

#     monkeypatch.setattr(ve.VenvContext, "run", fake_run, raising=True)

#     class DummyApp:
#         app_name = "second"

#     dev_command.apps = {"first-app": first_app_built, "second-app": DummyApp()}

#     with pytest.raises(UnsupportedCommandError):
#         dev_command(appname="second-app", run_app=True, update_requirements=False)

#     assert run_log.get("called") is True
#     assert (venv_path / "pyvenv.cfg").exists()


# def test_staticweb_app_does_not_exist_directory(dev_command, first_app):
#     """Raise error if the app doesn't exist in the project directory with multiple
#     apps."""

#     class DummyApp:
#         app_name = "second"

#     dev_command.apps = {
#         "first": first_app,
#         "second": DummyApp(),
#     }

#     with pytest.raises(BriefcaseCommandError) as exc:
#         dev_command(appname="non_existent_app", run_app=True, update_requirements=False)

#     assert "doesn't define an application named 'non_existent_app'" in str(exc.value)


# def test_staticweb_multiple_apps_no_app_given_triggers_else(dev_command, first_app):
#     """Raise error if multiple apps exist but no appname is provided."""

#     class DummyApp:
#         app_name = "second"

#     dev_command.apps = {
#         "first": first_app,
#         "second": DummyApp(),
#     }

#     with pytest.raises(BriefcaseCommandError) as exc:
#         dev_command(
#             None, run_app=True, update_requirements=False
#         )  # <- No appname provided!

#     assert "specifies more than one application" in str(exc.value)


# def test_staticweb_raises_unsupported_error(dev_command, first_app):
#     """Raise error if an unsupported command is called."""
#     dev_command.apps = {"first": first_app}

#     with pytest.raises(UnsupportedCommandError):
#         dev_command(
#             app=first_app,
#             run_app=True,
#             update_requirements=False,
#             no_isolation=False,
#         )
