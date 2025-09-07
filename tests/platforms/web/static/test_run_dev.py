import os

import pytest

from briefcase.exceptions import BriefcaseCommandError, UnsupportedCommandError
from briefcase.integrations import virtual_environment as ve
from briefcase.platforms.web.static import StaticWebDevCommand


@pytest.fixture
def dev_command(dummy_console, tmp_path):
    return StaticWebDevCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_web_dev_creates_venv_single_app_directory(
    monkeypatch, tmp_path, dev_command, first_app_built
):
    """StaticWebDevCommand creates a venv, then raises UnsupportedCommandError."""
    venv_path = (
        tmp_path / "base_path" / ".briefcase" / first_app_built.app_name / "venv"
    )
    run_log = {}

    # Fake subprocess.run to simulate venv creation
    def fake_run(self, args, check=True, **kwargs):
        run_log["called"] = True
        venv_path.mkdir(parents=True, exist_ok=True)
        (venv_path / "pyvenv.cfg").touch()
        (venv_path / ("Scripts" if os.name == "nt" else "bin")).mkdir(exist_ok=True)

    monkeypatch.setattr(ve.VenvContext, "run", fake_run, raising=True)

    dev_command.apps = {"first-app": first_app_built}

    with pytest.raises(UnsupportedCommandError):
        dev_command(app=first_app_built, run_app=True, update_requirements=False)

    assert run_log.get("called") is True
    assert (venv_path / "pyvenv.cfg").exists()


def test_staticweb_app_does_not_exist_directory(dev_command, first_app):
    """Raise error if the app doesn't exist in the project directory with multiple
    apps."""

    class DummyApp1:
        app_name = "non_existent_app"

    class DummyApp2:
        app_name = "second"

    dev_command.apps = {
        "first": first_app,
        "second": DummyApp2(),
    }

    with pytest.raises(BriefcaseCommandError) as exc:
        dev_command(app=DummyApp1(), run_app=True, update_requirements=False)

    assert "doesn't define an application named 'non_existent_app'" in str(exc.value)


def test_staticweb_multiple_apps_no_app_given_triggers_else(dev_command, first_app):
    """Raise error if multiple apps exist but no appname is provided."""

    class DummyApp:
        app_name = "second"

    dev_command.apps = {
        "first": first_app,
        "second": DummyApp(),
    }

    with pytest.raises(BriefcaseCommandError) as exc:
        dev_command(
            None, run_app=True, update_requirements=False
        )  # <- No appname provided!

    assert "specifies more than one application" in str(exc.value)


def test_staticweb_raises_unsupported_error(dev_command, first_app):
    """Raise error if an unsupported command is called."""
    dev_command.apps = {"first": first_app}

    with pytest.raises(UnsupportedCommandError):
        dev_command(
            app=first_app,
            run_app=True,
            update_requirements=False,
            no_isolation=False,
        )
