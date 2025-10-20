import importlib
from pathlib import Path

import pytest


def test_gitignore_write_oserror_is_wrapped(monkeypatch, tmp_path):
    new_mod = importlib.import_module("briefcase.commands.new")
    updater = getattr(new_mod, "_ensure_gitignore_briefcase", None)
    assert callable(updater), "Couldn't find _ensure_gitignore_briefcase in new.py"

    # Make any write/append attempt to .gitignore fail with OSError
    real_open = Path.open

    def boom_open(self, mode="r", *args, **kwargs):
        if any(ch in mode for ch in ("w", "a", "+")):
            raise OSError("disk full")
        return real_open(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", boom_open, raising=True)

    app_path = tmp_path / "demo-app"

    with pytest.raises(new_mod.BriefcaseConfigError) as excinfo:
        updater(app_path)

    msg = str(excinfo.value)
    assert "Unable to update" in msg and "disk full" in msg
