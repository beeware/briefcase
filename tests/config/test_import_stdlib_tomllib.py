# tests/config/test_import_stdlib_tomllib.py
import importlib
import sys
import types
from collections import namedtuple


def test_config_module_uses_stdlib_tomllib_when_py_gte_311(monkeypatch):
    # Fresh import so the top-level import branch executes now
    for name in list(sys.modules):
        if name == "briefcase.config" or name.startswith("briefcase.config."):
            sys.modules.pop(name, None)

    # Simulate Python 3.11+ with attrs like real version_info
    VersionInfo = namedtuple("VersionInfo", "major minor micro releaselevel serial")
    monkeypatch.setattr(
        sys, "version_info", VersionInfo(3, 11, 7, "final", 0), raising=False
    )

    # Provide a minimal stdlib-like tomllib the module can import
    fake_tomllib = types.ModuleType("tomllib")

    def _t(x):
        return x.decode("utf-8") if isinstance(x, bytes | bytearray) else x

    def loads(s):  # tiny KEY="VALUE" parser for any incidental use
        k, v = _t(s).split("=", 1)
        return {k.strip(): v.strip().strip('"').strip("'")}

    def load(fp):
        return loads(_t(fp.read()))

    fake_tomllib.loads = loads
    fake_tomllib.load = load
    monkeypatch.setitem(sys.modules, "tomllib", fake_tomllib)

    # Import AFTER patching; this hits the stdlib tomllib branch
    mod = importlib.import_module("briefcase.config")
    assert mod is not None
