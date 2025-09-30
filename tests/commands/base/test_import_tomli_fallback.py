import importlib
import sys
import types

import pytest


def test_base_import_uses_tomli_fallback_when_py_lt_311(monkeypatch, tmp_path):
    """Force briefcase.commands.base to take the 'tomli as tomllib' branch by simulating
    Python 3.10, provide a minimal fake 'tomli', and verify parse_config_overrides uses
    it successfully."""

    # 1) Remove any cached imports of the module under test.
    for name in list(sys.modules):
        if name == "briefcase.commands.base" or name.startswith(
            "briefcase.commands.base."
        ):
            sys.modules.pop(name, None)

    # 2) Make the interpreter "look" like 3.10 so the module chooses tomli.
    monkeypatch.setattr(sys, "version_info", (3, 10, 14), raising=False)

    # 3) Provide a tiny tomli shim (only what's needed by parse_config_overrides).
    fake_tomli = types.ModuleType("tomli")

    class TOMLDecodeError(ValueError):
        pass

    def loads(s):
        # parse_config_overrides passes a *string* like "foo=1"
        text = s.decode("utf-8") if isinstance(s, bytes | bytearray) else s
        if "Invalid" in text:
            raise TOMLDecodeError("broken")
        # Extremely tiny "parser": accept KEY=VALUE where VALUE is basic TOML
        # For our purposes, standard tomli would return a dict {"key": parsed_value}.
        key, value = text.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # A couple of quick types like toml would do:
        if value.isdigit():
            parsed = int(value)
        elif value.lower() in {"true", "false"}:
            parsed = value.lower() == "true"
        else:
            parsed = value
        return {key: parsed}

    fake_tomli.TOMLDecodeError = TOMLDecodeError
    fake_tomli.loads = loads
    monkeypatch.setitem(sys.modules, "tomli", fake_tomli)

    # 4) Import AFTER patching so the 'else: import tomli as tomllib' path is taken.
    base_mod = importlib.import_module("briefcase.commands.base")

    # 5) Sanity checks: valid override parses; invalid override raises BriefcaseCommandError.
    ok = base_mod.parse_config_overrides(["author='Jane'", "debug=true", "retries=3"])
    assert ok == {"author": "Jane", "debug": True, "retries": 3}

    # Disallow multi-level keys
    with pytest.raises(base_mod.BriefcaseConfigError):
        base_mod.parse_config_overrides(["nested.key=1"])

    # Disallow app_name override
    with pytest.raises(base_mod.BriefcaseConfigError):
        base_mod.parse_config_overrides(["app_name='Nope'"])

    # Invalid TOML content should be surfaced as BriefcaseConfigError
    with pytest.raises(base_mod.BriefcaseConfigError):
        base_mod.parse_config_overrides(["Invalid = thing"])
