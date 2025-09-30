from __future__ import annotations

import importlib
import sys
import types


def test_stdlib_tomllib_branch_is_exercised(monkeypatch, tmp_path):
    """Force the 'import tomllib' path in briefcase.commands.config to execute, even on
    Py<=3.10, by injecting a fake 'tomllib' then reloading the module."""
    import briefcase.commands.config as cfg_mod

    # Pretend we're on Python 3.11+
    monkeypatch.setattr(sys, "version_info", (3, 11, 0))

    # Provide a minimal tomllib shim so the try-import succeeds.
    fake = types.SimpleNamespace()

    def fake_load(fp):
        fp.read()
        return {"author": {"email": "user@example.com"}}

    fake.load = fake_load
    monkeypatch.setitem(sys.modules, "tomllib", fake)

    # Reload runs the top-level 'import tomllib' (line 9).
    cfg_mod = importlib.reload(cfg_mod)

    # Use the module so coverage ties through to the fake tomllib.
    p = tmp_path / "config.toml"
    p.write_bytes(b'author = { email = "user@example.com" }')
    data = cfg_mod.read_toml(p)
    assert data["author"]["email"] == "user@example.com"

    # Restore normal state for later tests.
    monkeypatch.delitem(sys.modules, "tomllib", raising=False)
