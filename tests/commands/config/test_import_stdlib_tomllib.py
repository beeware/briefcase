import importlib
import sys
import types


def test_config_import_uses_stdlib_tomllib_when_py_gte_311(monkeypatch, tmp_path):
    # Fresh import of the module under test
    for name in list(sys.modules):
        if name == "briefcase.commands.config" or name.startswith(
            "briefcase.commands.config."
        ):
            sys.modules.pop(name, None)

    # Pretend we are on Python 3.11+ so the module chooses 'tomllib'
    monkeypatch.setattr(sys, "version_info", (3, 11, 7), raising=False)

    # Minimal stdlib-like 'tomllib' with loads *and* load if your code uses both
    fake_tomllib = types.ModuleType("tomllib")

    def _t(x):
        return x.decode("utf-8") if isinstance(x, bytes | bytearray) else x

    def loads(s):
        text = _t(s)
        # Very small TOML 'parser' for the test
        key, value = text.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        return {key: value}

    def load(fp):
        return loads(_t(fp.read()))

    fake_tomllib.loads = loads
    fake_tomllib.load = load
    monkeypatch.setitem(sys.modules, "tomllib", fake_tomllib)

    cfg_mod = importlib.import_module("briefcase.commands.config")

    # Prove the branch by calling read_toml() which uses tomllib.{load,loads}
    p = tmp_path / "ok.toml"
    p.write_text('author = "Jane"', encoding="utf-8")
    data = cfg_mod.read_toml(p)
    assert data == {"author": "Jane"}
