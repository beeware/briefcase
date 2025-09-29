from __future__ import annotations

import tomli_w

import briefcase.commands.config as cfg_mod


def test_find_project_root_skips_on_load_error_and_uses_parent(tmp_path, monkeypatch):
    """If loading a child pyproject.toml raises a non-TOML error, the walker should
    'continue' and find the valid parent with [tool.briefcase]."""
    # parent with valid [tool.briefcase]
    parent = tmp_path / "proj"
    parent.mkdir()
    (parent / "pyproject.toml").write_text(
        tomli_w.dumps({"tool": {"briefcase": {"apps": {}}}}), encoding="utf-8"
    )

    # child with a pyproject that will raise during load
    child = parent / "a" / "b"
    child.mkdir(parents=True)
    bad = child / "pyproject.toml"
    bad.write_text("this can be anything", encoding="utf-8")

    # Make tomllib.load() raise at this path to hit 'except Exception: continue' (line 96).
    real_load = cfg_mod.tomllib.load

    def boom(fp):
        if fp.name == str(bad):
            raise RuntimeError("boom")
        return real_load(fp)

    monkeypatch.setattr(cfg_mod.tomllib, "load", boom)

    # Start walk inside child; should ignore the bad file and return parent.
    monkeypatch.chdir(child)
    assert cfg_mod.find_project_root() == parent
