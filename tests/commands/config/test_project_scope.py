from __future__ import annotations

import io
from pathlib import Path

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
    # Create a pyproject.toml at project root; content is irrelevant because we stub the loader.
    py = tmp_path / "pyproject.toml"
    py.write_text("# placeholder", encoding="utf-8")

    # Make the loader return a dict with [tool.briefcase] only for *this* file.
    import briefcase.commands.config as cfg_mod

    real_load = cfg_mod.tomllib.load

    def fake_load(fp):
        if getattr(fp, "name", "") == str(py):
            return {"tool": {"briefcase": {}}}
        return real_load(fp)

    monkeypatch.setattr(cfg_mod.tomllib, "load", fake_load)

    # Work inside a nested directory; finder must walk up to tmp_path
    (tmp_path / "sub" / "dir").mkdir(parents=True)
    monkeypatch.chdir(tmp_path / "sub" / "dir")

    cmd = ConfigCommand(console=DummyConsole())

    # project-scope SET
    cmd(key="author.name", value="Jane Developer", global_scope=False)

    p = tmp_path / ".briefcase" / "config.toml"
    assert p.exists()

    # project-scope LIST
    cmd.console.buf = io.StringIO()
    cmd(list=True, global_scope=False)
    out = cmd.console.getvalue()
    assert "author" in out and "Jane Developer" in out and "# file:" in out
    assert str(p) in out
