# tests/commands/new/test_import_stdlib_tomllib.py
import importlib
import sys
import types
from collections import namedtuple


def test_new_import_hits_tomllib_branch_when_py_gte_311(monkeypatch):
    # Fresh import so the top-level version check runs in this test
    for name in list(sys.modules):
        if name == "briefcase.commands.new" or name.startswith(
            "briefcase.commands.new."
        ):
            sys.modules.pop(name, None)

    # Simulate Python 3.11 with a version_info that has attrs (major/minor/etc.)
    VersionInfo = namedtuple("VersionInfo", "major minor micro releaselevel serial")
    monkeypatch.setattr(
        sys, "version_info", VersionInfo(3, 11, 7, "final", 0), raising=False
    )

    # Provide a minimal stdlib-like tomllib to satisfy any incidental loads (not strictly needed here)
    fake_tomllib = types.ModuleType("tomllib")
    fake_tomllib.loads = lambda s: {"k": "v"}
    monkeypatch.setitem(sys.modules, "tomllib", fake_tomllib)

    # Import AFTER patching; just importing exercises line 24
    mod = importlib.import_module("briefcase.commands.new")
    assert hasattr(mod, "NewCommand")
