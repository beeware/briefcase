import os
from pathlib import Path
from types import SimpleNamespace

from briefcase.commands import DevCommand
from briefcase.console import Console


class DummyDevEnvCommand(DevCommand):
    """DevCommand with a controllable app_module_path()."""

    def __init__(self, src_root: Path, *args, **kwargs):
        kwargs.setdefault("console", Console())
        super().__init__(*args, apps={}, **kwargs)
        self._src_root = src_root

    def app_module_path(self, app):
        return self._src_root / "__init__.py"


def test_app_dev_env_without_existing(tmp_path, first_app):
    """If PYTHONPATH isn't set, it is created with the app's src root."""
    src_root = tmp_path / "src" / first_app.module_name
    src_root.mkdir(parents=True, exist_ok=True)

    cmd = DummyDevEnvCommand(src_root=src_root, base_path=tmp_path)
    venv = SimpleNamespace(env={})

    env = cmd._app_dev_env(first_app, venv)

    assert env is not venv.env
    assert "PYTHONPATH" not in venv.env
    assert env["PYTHONPATH"] == os.fspath(src_root)


def test_app_dev_env_with_existing(tmp_path, first_app):
    """If PYTHONPATH is already set, src root is prepended."""
    src_root = tmp_path / "src" / first_app.module_name
    src_root.mkdir(parents=True, exist_ok=True)

    existing = "foo" + os.pathsep + "bar"
    venv = SimpleNamespace(env={"PYTHONPATH": existing, "X": "1"})

    cmd = DummyDevEnvCommand(src_root=src_root, base_path=tmp_path)
    env = cmd._app_dev_env(first_app, venv)

    expected = os.pathsep.join([os.fspath(src_root), existing])
    assert env["PYTHONPATH"] == expected
    assert env["X"] == "1"
