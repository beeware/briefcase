from __future__ import annotations

import importlib
import sys
import types

import tomli as real_tomli


def test_base_stdlib_tomllib_branch_is_exercised(monkeypatch, tmp_path):
    """Force the `if sys.version_info >= (3, 11): import tomllib` path in
    briefcase.commands.base (line 26) to execute on Py<=3.10 by injecting a fake
    'tomllib' and reloading the module.

    Then ensure that branch is actually used by calling parse_config_overrides().
    """
    # Import once to get a handle for reload
    import briefcase.commands.base as base_mod

    # 1) Fake a stdlib 'tomllib' that delegates to real tomli for correctness
    fake_tomllib = types.SimpleNamespace(
        loads=real_tomli.loads,
        load=real_tomli.load,
    )
    monkeypatch.setitem(sys.modules, "tomllib", fake_tomllib)

    # 2) Pretend we're on Python 3.11+ so the module chooses `import tomllib`
    monkeypatch.setattr(sys, "version_info", (3, 11, 0))

    # 3) Reload executes the top-level import branch (line 26)
    base_mod = importlib.reload(base_mod)

    # 4) Use a code path that calls tomllib.loads() to tie coverage through
    overrides = base_mod.parse_config_overrides(['description="Hello world"'])
    assert overrides == {"description": "Hello world"}

    # 5) Clean up: remove the fake and restore module to normal state
    monkeypatch.delitem(sys.modules, "tomllib", raising=False)
    importlib.reload(base_mod)
