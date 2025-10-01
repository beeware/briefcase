import importlib
import types

import pytest


def test_read_toml_file_invalid_raises(monkeypatch, tmp_path):
    cfg = importlib.import_module("briefcase.config")

    # Fake tomllib that always fails on load()
    class TOMLDecodeError(ValueError):
        pass

    def load(_fp):
        raise TOMLDecodeError("broken")

    fake_tomllib = types.SimpleNamespace(load=load, TOMLDecodeError=TOMLDecodeError)
    # Patch the module's tomllib so the except branch is guaranteed to run
    monkeypatch.setattr(cfg, "tomllib", fake_tomllib, raising=True)

    bad = tmp_path / "bad.toml"
    bad.write_text("does not matter", encoding="utf-8")

    with pytest.raises(cfg.BriefcaseConfigError) as exc:
        cfg.read_toml_file(bad)

    # Message contains the path and our error text
    assert "Invalid" in str(exc.value) and str(bad) in str(exc.value)


def test_read_toml_file_missing_returns_empty(tmp_path):
    cfg = importlib.import_module("briefcase.config")
    missing = tmp_path / "missing.toml"
    assert cfg.read_toml_file(missing) == {}
