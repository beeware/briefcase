# tests/commands/new/test_gitignore_briefcase.py
import importlib


def _read_lines(path):
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()]


def test_creates_gitignore_when_missing(tmp_path):
    new_mod = importlib.import_module("briefcase.commands.new")
    proj = tmp_path / "proj"
    assert not (proj / ".gitignore").exists()

    new_mod._ensure_gitignore_briefcase(proj)

    gi = proj / ".gitignore"
    assert gi.exists()
    lines = _read_lines(gi)
    assert ".briefcase/" in lines
    # idempotent re-run
    new_mod._ensure_gitignore_briefcase(proj)
    assert _read_lines(gi).count(".briefcase/") == 1


def test_appends_when_missing(tmp_path):
    new_mod = importlib.import_module("briefcase.commands.new")
    proj = tmp_path / "proj2"
    proj.mkdir()
    gi = proj / ".gitignore"
    gi.write_text("node_modules/\n.DS_Store\n", encoding="utf-8")

    new_mod._ensure_gitignore_briefcase(proj)

    lines = _read_lines(gi)
    assert "node_modules/" in lines
    assert ".DS_Store" in lines
    assert ".briefcase/" in lines
    assert lines.count(".briefcase/") == 1  # only appended once


def test_does_not_duplicate_if_present_with_whitespace(tmp_path):
    new_mod = importlib.import_module("briefcase.commands.new")
    proj = tmp_path / "proj3"
    proj.mkdir()
    gi = proj / ".gitignore"
    gi.write_text("  .briefcase/   \n", encoding="utf-8")

    new_mod._ensure_gitignore_briefcase(proj)

    # Still only one entry after normalization
    assert _read_lines(gi).count(".briefcase/") == 1


def test_creates_parent_directories(tmp_path):
    new_mod = importlib.import_module("briefcase.commands.new")
    nested = tmp_path / "nested" / "deeper" / "proj4"  # no parents yet

    new_mod._ensure_gitignore_briefcase(nested)

    gi = nested / ".gitignore"
    assert gi.exists()
    assert ".briefcase/" in _read_lines(gi)
