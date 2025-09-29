from __future__ import annotations

import argparse
import re
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

_CANONICAL_KEYS = {
    "author.name",
    "author.email",
    "android.device",
    "iOS.device",
    "macOS.identity",
    "macOS.xcode.identity",
}

_KEY_ALIASES = {
    "iOS.device": "ios.device",
    "macOS.identity": "macos.identity",
    "macOS.xcode.identity": "macos.xcode.identity",
}

_AVD_RE = re.compile(r"^@[\w.-]+$")
_EMULATOR_ID_RE = re.compile(r"^emulator-\d+$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_key(key: str) -> str:
    key = (key or "").strip()
    return _KEY_ALIASES.get(key, key.lower())


def validate_key(key: str, value: str) -> None:
    key = normalize_key(key)
    v = (value or "").strip()
    if not v:
        raise BriefcaseConfigError(f"Value for {key} cannot be empty.")

    if key not in _CANONICAL_KEYS:
        raise BriefcaseConfigError(
            f"Unknown configuration key: {key}. Allowed keys: {', '.join(sorted(_CANONICAL_KEYS))}"
        )

    # '?' sentinel is only allowed for device/identity keys
    if v == "?":
        if key in {
            "android.device",
            "iOS.device",
            "macOS.identity",
            "macOS.xcode.identity",
        }:
            return
        raise BriefcaseConfigError(
            "The '?' sentinel is only allowed for device/identity keys"
        )

    if key == "android.device":
        if v.startswith("@"):
            if _AVD_RE.match(v):
                return
            raise BriefcaseConfigError(
                "android.device AVD name must start with '@' e.g '@Pixel_5' "
            )
        if _EMULATOR_ID_RE.match(v):
            return
        raise BriefcaseConfigError(
            "Invalid android.device. Must be an AVD name (starting with '@') or an emulator ID (e.g., 'emulator-5554')"
        )

    if key == "author.name":
        return

    if key == "author.email":
        if not _EMAIL_RE.match(v):
            raise BriefcaseConfigError("author.email must be a valid email address.")
        return

    return


def scope_path(project_root: Path, is_global: bool) -> Path:
    if is_global:
        dirs = PlatformDirs("org.beeware.briefcase", "BeeWare")
        return Path(dirs.user_config_dir) / "config.toml"
    else:
        assert project_root is not None
        return project_root / ".briefcase" / "config.toml"


def find_project_root(start: Path | None = None) -> Path:
    """Resolve the Briefcase project root by TOML-parsing pyproject.toml and checking
    for [tool.briefcase]."""
    cur = (start or Path.cwd()).resolve()
    for parent in [cur, *cur.parents]:
        py = parent / "pyproject.toml"
        if not py.exists():
            continue
        try:
            with py.open("rb") as f:
                data = tomllib.load(f)
        except Exception:
            continue
        briefcase_tbl = data.get("tool", {}).get("briefcase")
        if isinstance(briefcase_tbl, dict):
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
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            tomli_w.dump(data or {}, f)
    except OSError as e:
        raise BriefcaseConfigError(f"Unable to write config file {path}: {e}") from e


def get_config(d: dict, dotted: str):
    cur = d
    for part in normalize_key(dotted).split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def set_config(d: dict, dotted: str, value):
    cur = d
    parts = normalize_key(dotted).split(".")
    for p in parts[:-1]:
        nxt = cur.setdefault(p, {})
        if not isinstance(nxt, dict):
            raise BriefcaseConfigError(f"Cannot set '{dotted}': '{p}' is not a table")
        cur = nxt
    cur[parts[-1]] = value
    return d


def unset_config(d: dict, dotted: str) -> bool:
    cur = d
    parts = normalize_key(dotted).split(".")
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            return False
        cur = cur[p]
    return cur.pop(parts[-1], None) is not None


class ConfigCommand(BaseCommand):
    """Command to modify Briefcase configuration settings.

    Allows setting of individual configuration keys within either a project-level or
    global configuration file. Useful for scripting or user-driven configuration outside
    of interactive prompts.
    """

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

        # Resolve the config path
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
                self.console.info(f"(empty)  [{path}]")
            else:
                self.console.print(tomli_w.dumps(data).rstrip())
                self.console.print(f"# file: {path}")
            return

        # SET
        if key and value is not None:
            key = normalize_key(key).strip()
            value = value.strip()

            parts = key.split(".")
            if any(not p.strip() for p in parts):
                raise BriefcaseConfigError(f"Invalid configuration key: {key}")

            validate_key(key, value)

            set_config(data, key, value)
            write_toml(path, data)
            self.console.info(
                f"Set {'global' if is_global else 'project'} config: {key} = {value}"
            )
            return

        raise BriefcaseConfigError("Invalid arguments for config command")

    def bundle_path(self, app):
        """A placeholder; Config command doesn't have a bundle path."""
        raise NotImplementedError()

    def binary_path(self, app):
        """A placeholder; Config command doesn't have a binary path."""
        raise NotImplementedError()

    def distribution_path(self, app):
        """A placeholder; Config command doesn't have a distribution path."""
        raise NotImplementedError()

    def binary_executable_path(self, app):
        """A placeholder; Config command doesn't have a binary executable path."""
        raise NotImplementedError()
