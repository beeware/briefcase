from __future__ import annotations

import argparse
import sys
from pathlib import Path

if sys.version_info >= (3, 11):  # pragma: no-cover-if-lt-py311
    import tomllib
else:  # pragma: no-cover-if-gte-py311
    import tomli as tomllib

import tomli_w
from platformdirs import PlatformDirs

from briefcase.commands.base import BaseCommand
from briefcase.exceptions import BriefcaseConfigError


def scope_path(project_root: Path, is_global: bool) -> Path:
    if is_global:
        dir = PlatformDirs("org.beeware.briefcase", "BeeWare")
        return Path(dir.user_config_dir) / "config.toml"
    else:
        return project_root / ".briefcase" / "config.toml"


def find_project_root(start: Path | None = None) -> Path:
    """Resolve the Briefcase project root by walking up from cwd."""
    cur = (start or Path.cwd()).resolve()
    for parent in [cur, *cur.parents]:
        py = parent / "pyproject.toml"
        if py.exists():
            content = py.read_text(encoding="utf-8", errors="ignore")
            if "[tool.briefcase]" in content:
                return parent
    raise BriefcaseConfigError(
        "Not a Briefcase project: no pyproject.toml with [tool.briefcase] found "
        f"starting from {cur}"
    )


def read_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise BriefcaseConfigError(f"Invalid TOML in {path}: {e}") from e


def normalize_briefcase_root(data: dict) -> dict:
    """Accept files that either mirror [tool.briefcase] or store keys at root."""
    if isinstance(data, dict) and "tool" in data:
        tb = data.get("tool", {}).get("briefcase")
        if isinstance(tb, dict):
            return tb
    return data or {}


def write_toml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        tomli_w.dump(data or {}, f)


def get_config(d: dict, dotted: str):
    cur = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def set_config(d: dict, dotted: str, value):
    cur = d
    parts = dotted.split(".")
    for p in parts[:-1]:
        nxt = cur.setdefault(p, {})
        if not isinstance(nxt, dict):
            raise BriefcaseConfigError(f"Cannot set '{dotted}': '{p}' is not a table")
        cur = nxt
    cur[parts[-1]] = value
    return d


def unset_config(d: dict, dotted: str) -> bool:
    cur = d
    parts = dotted.split(".")
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            return False
        cur = cur[p]
    return cur.pop(parts[-1], None) is not None


class ConfigCommand(BaseCommand):
    command = "config"
    platform = None
    output_format = None
    description = "Configure per-project or global user configurations"
    help = "Configure per-project or global settings"

    def add_options(self, parser: argparse.ArgumentParser) -> None:
        super().add_options(parser)

        parser.add_argument(
            "--global",
            dest="global_scope",
            action="store_true",
            help="Use global per-user config",
        )

        mode = parser.add_mutually_exclusive_group()
        mode.add_argument(
            "--get", metavar="KEY", help="Print a value from the chosen scope"
        )
        mode.add_argument(
            "--unset", metavar="KEY", help="Remove a key from the chosen scope"
        )
        mode.add_argument(
            "--list", action="store_true", help="List the chosen scope's config"
        )

        parser.add_argument(
            "key",
            nargs="?",
            help="Key to set (dotted path, e.g., macOS.xcode.identity)",
        )
        parser.add_argument("value", nargs="?", help="Value to set (string)")

    def __call__(self, app=None, **options):
        is_global = bool(options.get("global_scope", False))

        if is_global:
            project_root = None
            path = scope_path(project_root, is_global=True)
        else:
            project_root = find_project_root()
            path = scope_path(project_root, is_global=False)

        key = options.get("key")
        value = options.get("value")
        get_key = options.get("get")
        unset_key = options.get("unset")
        do_list = bool(options.get("list"))

        # Validate exactly one operation
        op_count = sum(
            bool(x) for x in [get_key, unset_key, do_list, (key and value is not None)]
        )
        if op_count == 0:
            raise BriefcaseConfigError(
                "No operation. Use one: --get KEY | --unset KEY | --list | KEY VALUE"
            )
        if op_count > 1:
            raise BriefcaseConfigError(
                "Multiple operations. Use only one: --get KEY | --unset KEY | --list | KEY VALUE"
            )

        data = normalize_briefcase_root(read_toml(path))

        # GET
        if get_key:
            result = get_config(data, get_key)
            if result is None:
                self.console.warning(f"{get_key} not set in {path}")
            else:
                self.console.print(f"{result}")
            return

        # UNSET
        if unset_key:
            if unset_config(data, unset_key):
                write_toml(path, data)
                self.console.info(f"Unset {unset_key} in {path}")
            else:
                self.console.warning(f"{unset_key} not present in {path}")
            return

        # LIST
        if do_list:
            if not data:
                self.console.info(f"(empty)  [{[path]}]")
            else:
                self.console.print(tomli_w.dumps(data).rstrip())
                self.console.print(f"# file: {path}")

        # SET
        if key and value is not None:
            parts = key.split(".")
            if any(not p.strip() for p in parts):
                raise BriefcaseConfigError(f"Invalid configuration key: {key}")
            set_config(data, key, value)
            write_toml(path, data)
            self.console.info(
                f"Set {'global' if is_global else 'project'} config: {key} = {value}"
            )
            return

        raise BriefcaseConfigError("Invalid arguments for config command")
