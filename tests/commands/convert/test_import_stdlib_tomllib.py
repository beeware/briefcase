# tests/commands/convert/test_import_stdlib_tomllib.py
import importlib
import sys
import types
from collections import namedtuple
from pathlib import Path


def test_convert_import_uses_stdlib_tomllib_when_py_gte_311(monkeypatch, tmp_path):
    # 1) Fresh import of the module under test so the import branch runs now.
    for name in list(sys.modules):
        if name == "briefcase.commands.convert" or name.startswith(
            "briefcase.commands.convert."
        ):
            sys.modules.pop(name, None)

    # 2) Pretend we’re on Python 3.11+ so the module chooses stdlib 'tomllib'.
    VersionInfo = namedtuple("VersionInfo", "major minor micro releaselevel serial")
    monkeypatch.setattr(
        sys, "version_info", VersionInfo(3, 11, 7, "final", 0), raising=False
    )

    # 3) Provide a minimal stdlib-like 'tomllib' with load/loads.
    fake_tomllib = types.ModuleType("tomllib")

    def _t(x):
        return x.decode("utf-8") if isinstance(x, bytes | bytearray) else x

    def loads(s):
        text = _t(s)
        # very tiny parser for KEY="VALUE"
        key, value = text.split("=", 1)
        return {key.strip(): value.strip().strip('"').strip("'")}

    def load(fp):
        return loads(_t(fp.read()))

    fake_tomllib.loads = loads
    fake_tomllib.load = load
    monkeypatch.setitem(sys.modules, "tomllib", fake_tomllib)

    # 4) Import AFTER patching to take the tomllib path.
    convert_mod = importlib.import_module("briefcase.commands.convert")

    # 5) Create a minimal pyproject and point the command at it.
    (tmp_path / "pyproject.toml").write_text('author = "Jane"', encoding="utf-8")

    class DummyConsole:
        def print(self, *a, **k):
            pass

        def info(self, *a, **k):
            pass

        def warning(self, *a, **k):
            pass

        def error(self, *a, **k):
            pass

        def divider(self, *a, **k):
            pass

        def prompt(self, *a, **k):
            pass

        def text_question(self, *a, **k):
            return ""

        def selection_question(self, *a, **k):
            return ""

    cmd = convert_mod.ConvertCommand(console=DummyConsole())
    # Ensure the command looks in our temp project dir
    cmd.base_path = Path(tmp_path)

    # Access the cached_property that uses tomllib.load under the hood.
    data = cmd.pyproject
    assert data == {"author": "Jane"}

    # And validate the file; should not raise since it has no [tool.briefcase].
    cmd.validate_pyproject_file()
