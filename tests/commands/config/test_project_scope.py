from __future__ import annotations

import io
from pathlib import Path

import tomli_w

from briefcase.commands.config import ConfigCommand


class DummyConsole:
    def __init__(self):
        self.buf = io.StringIO()

    def print(self, *a, **k):
        self.buf.write(" ".join(map(str, a)) + "\n")

    def info(self, *a, **k):
        self.buf.write(" ".join(map(str, a)) + "\n")

    def warning(self, *a, **k):
        self.buf.write(" ".join(map(str, a)) + "\n")

    def getvalue(self):
        return self.buf.getvalue()


def _project_scope_path(root: Path) -> Path:
    return root / ".briefcase" / "config.toml"


def test_project_scope_set_and_list_inside_project(tmp_path, monkeypatch):
    """Inside a Briefcase project, project-scope write and list use
    .briefcase/config.toml."""
    # Arrange a minimal project with pyproject.toml containing [tool.briefcase]
    py = tmp_path / "pyproject.toml"
    py.write_text(
        tomli_w.dumps({"tool": {"briefcase": {"apps": {}}}}), encoding="utf-8"
    )

    # cd into a subdir; find_project_root must walk up and find tmp_path
    (tmp_path / "sub" / "dir").mkdir(parents=True)
    monkeypatch.chdir(tmp_path / "sub" / "dir")

    cmd = ConfigCommand(console=DummyConsole())

    # Act: project-scope SET
    cmd(key="author.name", value="Jane Developer", global_scope=False)

    # Assert: wrote to .briefcase/config.toml under the project root
    p = _project_scope_path(tmp_path)
    assert p.exists(), "project-scope config should be created under .briefcase/"

    # Act: LIST (non-empty path)
    cmd.console.buf = io.StringIO()
    cmd(list=True, global_scope=False)
    out = cmd.console.getvalue()

    # Assert: non-empty list includes serialized key and a file trailer line
    assert "author" in out and "Jane Developer" in out and "# file:" in out
    assert str(p) in out
