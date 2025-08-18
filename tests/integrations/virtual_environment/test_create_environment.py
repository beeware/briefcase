import subprocess
import sys
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.virtual_environment import (
    NoOpEnvironment,
    VenvEnvironment,
    VenvRunner,
    pip_install_generic,
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


def test_rewrite_head_no_args(dummy_tools, tmp_path):
    """Test that rewrite_head returns an empty list when no args are provided."""
    runner = VenvRunner(dummy_tools, tmp_path)
    assert runner._rewrite_head([]) == []


def test_rewrite_head_with_matching_args(dummy_tools, tmp_path):
    """Test that rewrite_head returns the matching interpreter and remaining args."""
    runner = VenvRunner(dummy_tools, tmp_path)
    assert runner._rewrite_head(["python", "args1"]) == [runner.executable, "args1"]


def test_rewrite_head_with_no_matching_args(dummy_tools, tmp_path):
    """Test that rewrite_head returns the original args when no matching interpreter is
    found."""
    runner = VenvRunner(dummy_tools, tmp_path)
    assert runner._rewrite_head(["args1", "args2"]) == ["args1", "args2"]


def test_popen_returns_process(dummy_tools, tmp_path):
    """Test that Popen returns a process object and calls subprocess.Popen with the
    correct arguments."""
    runner = VenvRunner(dummy_tools, tmp_path)

    runner.Popen(["python", "args1", "args2"])
    dummy_tools.subprocess.Popen.assert_called_once_with(
        [runner.executable, "args1", "args2"],
        env=runner.env,
    )


def test_pip_install_generic_no_requirements(tmp_path, dummy_console, dummy_tools):
    """Test pip_install_generic with no requirements returns nothing."""
    pip_install_generic(dummy_tools, dummy_console, [], venv_path=tmp_path)
    dummy_tools.subprocess.run.assert_not_called()


def test_pip_install_generic_with_requirements(dummy_console, dummy_tools):
    """Test pip_install_generic with requirements, deep debug and extra args."""
    pip_install_generic(
        dummy_tools,
        dummy_console,
        ["req1", "req2"],
        extra_args=["extra1"],
        deep_debug=True,
    )
    dummy_tools.subprocess.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "-vv",
            "extra1",
            "req1",
            "req2",
        ],
        check=True,
        encoding="UTF-8",
        env=mock.ANY,
    )


def test_pip_install_generic_no_deep_debug(dummy_console, dummy_tools):
    """Test pip_install_generic with no deep debug."""
    pip_install_generic(
        dummy_tools,
        dummy_console,
        ["req1", "req2"],
        extra_args=["extra1"],
        deep_debug=False,
    )
    dummy_tools.subprocess.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "extra1",
            "req1",
            "req2",
        ],
        check=True,
        encoding="UTF-8",
        env=mock.ANY,
    )


def test_pip_install_generic_no_extra_args(dummy_console, dummy_tools):
    """Test pip_install_generic with no extra args."""
    pip_install_generic(
        dummy_tools,
        dummy_console,
        ["req1", "req2"],
        deep_debug=True,
    )
    dummy_tools.subprocess.run.assert_called_once_with(
        [
            sys.executable,
            "-u",
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "-vv",
            "req1",
            "req2",
        ],
        check=True,
        encoding="UTF-8",
        env=mock.ANY,
    )


def test_virtual_environment_creates_venv(tmp_path, dummy_console, dummy_tools):
    app = DummyApp()
    env = VenvEnvironment(
        dummy_tools, dummy_console, tmp_path, app, upgrade_bootstrap=False
    )

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

    assert isinstance(result, VenvRunner)


def test_virtual_environment_upgrade_bootstrap_error(
    tmp_path, dummy_console, dummy_tools
):
    """Test error in upgrading the bootstrap is handled gracefully."""
    app = DummyApp()
    env = VenvEnvironment(
        dummy_tools, dummy_console, tmp_path, app, upgrade_bootstrap=True
    )

    with mock.patch(
        "subprocess.run",
        side_effect=[None, subprocess.CalledProcessError(1, cmd="python")],
    ):
        with pytest.raises(BriefcaseCommandError) as excinfo:
            env.__enter__()
        assert (
            f"Virtual environment created, but failed to bootstrap pip tooling for {app.app_name}"
            in str(excinfo.value)
        )


def test_virtual_environment_recreate(tmp_path, dummy_console, dummy_tools):
    """Test the old virtual environment is deleted and recreated."""
    app = DummyApp()
    venv_dir = tmp_path / ".briefcase" / app.app_name / "venv"
    venv_dir.mkdir(parents=True, exist_ok=True)
    (venv_dir / "pyvenv.cfg").touch()

    pyvenv_cfg = tmp_path / ".briefcase" / app.app_name / "venv" / "pyvenv.cfg"
    venv_root = pyvenv_cfg.parent

    env = VenvEnvironment(
        dummy_tools,
        dummy_console,
        tmp_path,
        app,
        recreate=True,
        upgrade_bootstrap=False,
    )

    with mock.patch("subprocess.run") as mock_run:
        result = env.__enter__()
        assert not venv_dir.exists()
        mock_run.assert_called_once_with(
            [
                sys.executable,
                "-m",
                "venv",
                str(venv_root),
            ],
            check=True,
        )

    assert isinstance(result, VenvRunner)


def test_virtual_environment_skips_if_exists(tmp_path, dummy_console, dummy_tools):
    app = DummyApp()
    venv_path = tmp_path / ".briefcase" / app.app_name / "venv"
    pyvenv_cfg = venv_path / "pyvenv.cfg"
    pyvenv_cfg.parent.mkdir(parents=True, exist_ok=True)
    pyvenv_cfg.touch()

    env = VenvEnvironment(
        dummy_tools, dummy_console, tmp_path, app, upgrade_bootstrap=False
    )

    with mock.patch("subprocess.run") as mock_run:
        result = env.__enter__()
        mock_run.assert_not_called()

    assert isinstance(result, VenvRunner)


def test_virtual_environment_creation_failure(tmp_path, dummy_console, dummy_tools):
    app = DummyApp()
    env = VenvEnvironment(dummy_tools, dummy_console, tmp_path, app)

    with mock.patch(
        "subprocess.run", side_effect=subprocess.CalledProcessError(1, cmd="python")
    ):
        with pytest.raises(BriefcaseCommandError) as excinfo:
            env.__enter__()
        assert "Failed to create virtual environment" in str(excinfo.value)


def test_virtual_environment_missing_appname_file(tmp_path, dummy_console, dummy_tools):
    """Ensure venv is created when .briefcase exists but app_name directory is
    missing."""
    app = DummyApp()

    # Create .briefcase directory only
    briefcase_dir = tmp_path / ".briefcase"
    briefcase_dir.mkdir(parents=True, exist_ok=True)

    # Simulate app_name directory does not exist
    app_dir = briefcase_dir / app.app_name
    assert not app_dir.exists()

    env = VenvEnvironment(
        dummy_tools, dummy_console, tmp_path, app, upgrade_bootstrap=False
    )
    venv_path = app_dir / "venv"

    with mock.patch("subprocess.run") as mock_run:
        result = env.__enter__()
        mock_run.assert_called_once_with(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
        )

    assert isinstance(result, VenvRunner)


def test_virtual_environment_missing_venv_file(tmp_path, dummy_console, dummy_tools):
    """Ensure venv is created when .briefcase/app_name exists but venv directory is
    missing."""
    app = DummyApp()

    # Create .briefcase/app_name directory only
    briefcase_dir = tmp_path / ".briefcase" / app.app_name
    briefcase_dir.mkdir(parents=True, exist_ok=True)

    # Simulate venv directory does not exist
    venv_dir = briefcase_dir / "venv"
    assert not venv_dir.exists()

    env = VenvEnvironment(
        dummy_tools, dummy_console, tmp_path, app, upgrade_bootstrap=False
    )
    venv_path = venv_dir

    with mock.patch("subprocess.run") as mock_run:
        result = env.__enter__()
        mock_run.assert_called_once_with(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
        )

    assert isinstance(result, VenvRunner)


def test_virtual_environment_exit(tmp_path, dummy_console, dummy_tools):
    """Ensure __exit__() returns False for context manager."""
    app = DummyApp()
    env = VenvEnvironment(dummy_tools, dummy_console, tmp_path, app)
    assert env.__exit__(None, None, None) is False


def test_noop_environment_returns_sys_prefix(tmp_path, dummy_console, dummy_tools):
    app = DummyApp()
    env = NoOpEnvironment(dummy_tools, dummy_console, tmp_path, app)
    result = env.__enter__()
    assert isinstance(result, VenvRunner)


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
