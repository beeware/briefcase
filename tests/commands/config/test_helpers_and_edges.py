import importlib
import types
from pathlib import Path

import pytest

cfg = importlib.import_module("briefcase.commands.config")


class DummyConsole:
    def print(self, *a, **k):
        pass

    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass


# normalize_key() returns trimmed string, handles None
def test_normalize_key_trims_and_handles_none():
    assert cfg.normalize_key("  android.device  ") == "android.device"
    assert cfg.normalize_key(None) == ""


# android.device startswith '@' but invalid -> specific error branch
def test_validate_key_android_avd_name_with_space_rejected():
    with pytest.raises(cfg.BriefcaseConfigError) as exc:
        cfg.validate_key("android.device", "@Pixel 5")  # space breaks the AVD regex
    assert "must start with '@'" in str(exc.value) or "AVD name" in str(exc.value)


# author.email valid path returns (no error)
def test_validate_key_author_email_valid_ok():
    # Should not raise
    cfg.validate_key("author.email", "user@example.com")


# find_project_root() continues on missing/invalid and then finds; also raises when none
def test_find_project_root_walks_parents_and_skips_invalid(tmp_path):
    # Build nested structure: start -> C -> B -> A -> ROOT
    root = tmp_path / "root"
    A = root / "A"
    B = A / "B"
    C = B / "C"
    C.mkdir(parents=True)

    # A has a *pyproject* but with invalid TOML -> triggers the 'except: continue' branch
    (A / "pyproject.toml").write_text("Invalid = [,,,]", encoding="utf-8")

    # ROOT has a valid pyproject with [tool.briefcase] -> should be returned
    (root / "pyproject.toml").write_text(
        '[tool.briefcase]\nproject_name="ok"\n', encoding="utf-8"
    )

    found = cfg.find_project_root(start=C)
    assert found == root


def test_find_project_root_raises_when_no_marker(tmp_path):
    # No pyproject anywhere
    with pytest.raises(cfg.BriefcaseConfigError):
        cfg.find_project_root(start=tmp_path)


# normalize_briefcase_root extracts [tool.briefcase] ----
def test_normalize_briefcase_root_extracts_tool_section():
    data = {"tool": {"briefcase": {"author": {"name": "Jane"}}}}
    assert cfg.normalize_briefcase_root(data) == {"author": {"name": "Jane"}}

    # also accepts already-flat dicts (returns as-is)
    assert cfg.normalize_briefcase_root({"author": {"email": "x@ex.com"}}) == {
        "author": {"email": "x@ex.com"}
    }


# set_config raises when an intermediate part isn't a table
def test_set_config_raises_when_parent_not_table():
    d = {"author": "someone"}  # 'author' is not a dict/table
    with pytest.raises(cfg.BriefcaseConfigError):
        cfg.set_config(d, "author.name", "Jane")


# __call__ detects "multiple operations"
def test_call_multiple_operations_error(monkeypatch, tmp_path):
    cmd = cfg.ConfigCommand(console=DummyConsole())

    fake_path = tmp_path / "config.toml"
    monkeypatch.setattr(cfg, "find_project_root", lambda: tmp_path, raising=True)
    monkeypatch.setattr(cfg, "scope_path", lambda *a, **k: fake_path, raising=True)
    monkeypatch.setattr(cfg, "read_toml", lambda _p: {}, raising=True)

    with pytest.raises(cfg.BriefcaseConfigError) as exc:
        cmd.__call__(
            global_scope=False,
            get="author.name",
            unset=None,
            list=False,
            key="author.email",
            value="x@ex.com",
        )
    assert "Multiple operations" in str(exc.value)


def test_call_set_invalid_key_with_blank_segment(monkeypatch, tmp_path):
    cmd = cfg.ConfigCommand(console=DummyConsole())

    fake_path = tmp_path / "config.toml"
    monkeypatch.setattr(cfg, "find_project_root", lambda: tmp_path, raising=True)
    monkeypatch.setattr(cfg, "scope_path", lambda *a, **k: fake_path, raising=True)
    monkeypatch.setattr(cfg, "read_toml", lambda _p: {}, raising=True)

    with pytest.raises(cfg.BriefcaseConfigError) as exc:
        cmd.__call__(
            global_scope=False,
            get=None,
            unset=None,
            list=False,
            key="author..email",
            value="user@example.com",
        )
    assert "Invalid configuration key" in str(exc.value)


def test_validate_key_default_passthrough():
    # Hits the final return in validate_key (no special-case logic)
    assert cfg.validate_key("author.name", "Jane Smith") is None


def test_project_root_returns_start_when_briefcase_present(tmp_path, monkeypatch):
    """Covers isinstance(..., dict) == True at the start dir (line 113)."""
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "pyproject.toml").write_text("ignored", encoding="utf-8")

    class FakeTomllib(types.SimpleNamespace):
        class TOMLDecodeError(ValueError): ...

    def fake_load(fp):
        return {"tool": {"briefcase": {}}}

    monkeypatch.setattr(cfg, "tomllib", FakeTomllib(load=fake_load), raising=True)

    assert cfg.find_project_root(start=proj) == proj


def test_project_root_walks_parents_to_find_briefcase(tmp_path, monkeypatch):
    """Covers the loop header (line 103) and then True at line 113 in parent."""
    root = tmp_path / "root"
    child = root / "child"
    child.mkdir(parents=True)
    child_py = child / "pyproject.toml"
    root_py = root / "pyproject.toml"
    child_py.write_text("ignored", encoding="utf-8")
    root_py.write_text("ignored", encoding="utf-8")

    def fake_load(fp):
        p = Path(fp.name)
        if p == child_py:
            return {"tool": {"something": 1}}  # no briefcase -> skip
        if p == root_py:
            return {"tool": {"briefcase": {}}}  # briefcase -> return
        return {}

    class FakeTomllib(types.SimpleNamespace):
        class TOMLDecodeError(ValueError): ...

    monkeypatch.setattr(cfg, "tomllib", FakeTomllib(load=fake_load), raising=True)

    assert cfg.find_project_root(start=child) == root


def test_validate_key_hits_final_return_via_temp_allowlist(monkeypatch):
    # Make a temporary allowed key that has no special-case logic
    monkeypatch.setattr(
        cfg,
        "_ALLOWED_KEYS",
        set(cfg._ALLOWED_KEYS) | {"android.sdk_path"},
        raising=True,
    )
    assert cfg.validate_key("android.sdk_path", "/opt/android-sdk") is None


def test_normalize_briefcase_root_passthrough_non_dict():
    # Non-dict input passes through unchanged
    assert cfg.normalize_briefcase_root(123) == 123
    assert cfg.normalize_briefcase_root("briefcase") == "briefcase"
    assert cfg.normalize_briefcase_root(None) == {}


def test_normalize_root_briefcase_non_dict_passthrough():
    # tool.briefcase present but not a dict → function returns the original dict
    data = {"tool": {"briefcase": "yes"}}
    assert cfg.normalize_briefcase_root(data) == data


def test_normalize_root_empty_dict_returns_empty():
    # empty dict → falls through to "data or {}" → {}
    assert cfg.normalize_briefcase_root({}) == {}
