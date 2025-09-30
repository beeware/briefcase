import builtins
import importlib
import sys
import types


def test_tomli_fallback_branch_is_exercised(monkeypatch, tmp_path):
    # fresh import
    for name in list(sys.modules):
        if name == "briefcase.commands.config" or name.startswith(
            "briefcase.commands.config."
        ):
            sys.modules.pop(name, None)

    # block tomllib import globally
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "tomllib":
            raise ModuleNotFoundError("force tomli fallback")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import, raising=True)
    sys.modules.pop("tomllib", None)

    # minimal tomli
    fake_tomli = types.ModuleType("tomli")

    class TOMLDecodeError(Exception):
        pass

    def _t(x):
        return x.decode("utf-8") if isinstance(x, bytes | bytearray) else x

    def loads(s):
        s = _t(s)
        if "Invalid" in s:
            raise TOMLDecodeError("broken")
        return {"author": {"email": "x@example.com"}}

    def load(fp):
        s = _t(fp.read())
        if "Invalid" in s:
            raise TOMLDecodeError("broken")
        return {"author": {"email": "x@example.com"}}

    fake_tomli.TOMLDecodeError = TOMLDecodeError
    fake_tomli.loads = loads
    fake_tomli.load = load
    monkeypatch.setitem(sys.modules, "tomli", fake_tomli)

    cfg = importlib.import_module("briefcase.commands.config")

    p = tmp_path / "ok.toml"
    p.write_text('author = { email = "x@example.com" }', encoding="utf-8")
    data = cfg.read_toml(p)
    assert data["author"]["email"] == "x@example.com"
