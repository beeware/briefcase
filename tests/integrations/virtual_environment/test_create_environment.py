import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.virtual_environment import (
    NoOpEnvironment,
    VenvEnvironment,
    virtual_environment,
)


class DummyApp:
    def __init__(self, app_name="myapp"):
        self.app_name = app_name


@pytest.fixture
def dummy_console():
    return mock.MagicMock()


@pytest.fixture
def dummy_tools(tmp_path):
    tools = mock.MagicMock()
    tools.subprocess = mock.MagicMock()
    tools.base_path = tmp_path
    tools.home_path = tmp_path
    tools.console = mock.MagicMock()
    tools.host_os = "Linux"
    tools.os.environ = {}
    return tools


@pytest.fixture
def dummy_app():
    return DummyApp()


def test_virtual_environment_creates_venv(tmp_path, dummy_console, dummy_tools):
    app = DummyApp()
    env = VenvEnvironment(dummy_tools, dummy_console, tmp_path, app)

    pyvenv_cfg = tmp_path / ".briefcase" / app.app_name / "venv" / "pyvenv.cfg"
    venv_root = pyvenv_cfg.parent

    # Simulate venv not existing
    assert not pyvenv_cfg.exists()

    with mock.patch("subprocess.run") as mock_run:
        result = env.__enter__()
        mock_run.assert_called_once_with(
            [
                sys.executable,
                "-m",
                "venv",
                str(venv_root),
            ],
            check=True,
        )

    assert result == venv_root


def test_virtual_environment_skips_if_exists(tmp_path, dummy_console, dummy_tools):
    app = DummyApp()
    venv_path = tmp_path / ".briefcase" / app.app_name / "venv"
    pyvenv_cfg = venv_path / "pyvenv.cfg"
    pyvenv_cfg.parent.mkdir(parents=True, exist_ok=True)
    pyvenv_cfg.touch()

    env = VenvEnvironment(dummy_tools, dummy_console, tmp_path, app)

    with mock.patch("subprocess.run") as mock_run:
        result = env.__enter__()
        mock_run.assert_not_called()

    assert result == venv_path


def test_virtual_environment_creation_failure(tmp_path, dummy_console, dummy_tools):
    app = DummyApp()
    env = VenvEnvironment(dummy_tools, dummy_console, tmp_path, app)

    with mock.patch(
        "subprocess.run", side_effect=subprocess.CalledProcessError(1, cmd="python")
    ):
        with pytest.raises(BriefcaseCommandError) as excinfo:
            env.__enter__()
        assert "Failed to create virtual environment" in str(excinfo.value)


def test_virtual_environment_exit(tmp_path, dummy_console, dummy_tools):
    """Ensure __exit__() returns False for context manager."""
    app = DummyApp()
    env = VenvEnvironment(dummy_tools, dummy_console, tmp_path, app)
    assert env.__exit__(None, None, None) is False


def test_noop_environment_returns_sys_prefix(tmp_path, dummy_console, dummy_tools):
    app = DummyApp()
    env = NoOpEnvironment(dummy_tools, dummy_console, tmp_path, app)
    result = env.__enter__()
    assert result == Path(sys.prefix)


def test_noop_environment_exit(tmp_path, dummy_console, dummy_tools):
    """Ensure __exit__() returns False for NoOp context manager."""
    app = DummyApp()
    env = NoOpEnvironment(dummy_tools, dummy_console, tmp_path, app)
    assert env.__exit__(None, None, None) is False


def test_virtual_environment_factory_no_isolation(
    tmp_path, dummy_console, dummy_tools, dummy_app
):
    env = virtual_environment(
        tools=dummy_tools,
        console=dummy_console,
        base_path=tmp_path,
        app=dummy_app,
        no_isolation=True,
    )
    assert isinstance(env, NoOpEnvironment)


def test_virtual_environment_factory_isolated(
    tmp_path, dummy_console, dummy_tools, dummy_app
):
    env = virtual_environment(
        tools=dummy_tools, console=dummy_console, base_path=tmp_path, app=dummy_app
    )
    assert isinstance(env, VenvEnvironment)
