import importlib
import sys
import types


def test_base_import_uses_stdlib_tomllib_when_py_gte_311(monkeypatch):
    # Fresh import of the module under test
    for name in list(sys.modules):
        if name == "briefcase.commands.base" or name.startswith(
            "briefcase.commands.base."
        ):
            sys.modules.pop(name, None)

    # Pretend we are on Python 3.11+ so the module chooses 'tomllib'
    monkeypatch.setattr(sys, "version_info", (3, 11, 7), raising=False)

    # Provide a minimal stdlib-like 'tomllib'
    fake_tomllib = types.ModuleType("tomllib")

    def _t(x):
        return x.decode("utf-8") if isinstance(x, bytes | bytearray) else x

    def loads(s):
        text = _t(s)
        key, value = text.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # Do a couple of simple type normalizations
        if value.isdigit():
            parsed = int(value)
        elif value.lower() in {"true", "false"}:
            parsed = value.lower() == "true"
        else:
            parsed = value
        return {key: parsed}

    fake_tomllib.loads = loads
    monkeypatch.setitem(sys.modules, "tomllib", fake_tomllib)

    base_mod = importlib.import_module("briefcase.commands.base")

    # Use a function that relies on tomllib to prove the path was taken
    out = base_mod.parse_config_overrides(["author='Jane'", "debug=true", "retries=3"])
    assert out == {"author": "Jane", "debug": True, "retries": 3}
