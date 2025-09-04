from __future__ import annotations

import enum
import json
from abc import ABC, abstractmethod
from importlib import metadata
from pathlib import Path
from typing import TypedDict

import briefcase


def _is_editable_pep610(dist_name: str) -> bool:
    """Check if briefcase is installed as editable build.

    The check requires, that the tool that installs briefcase support PEP610 (eg. pip
    since v20.1).
    """
    try:
        dist = metadata.distribution(dist_name)
    except metadata.PackageNotFoundError:
        raise

    direct_url = dist.read_text("direct_url.json")
    if direct_url is None:
        return False

    try:
        data = json.loads(direct_url)
        return data.get("dir_info", {}).get("editable", False)
    except Exception:
        return False


IS_EDITABLE = _is_editable_pep610("briefcase")
REPO_ROOT = Path(__file__).parent.parent.parent.parent if IS_EDITABLE else None


def get_debugger_requirement(package_name: str, extras: str = ""):
    """Get the requirement of a debugger support package.

    On editable installs of briefcase the path to the local package is used, to simplify
    the development of the debugger support packages. On normal installs the local
    version is not available, so the package from pypi is used, that corresponds to the
    version of briefcase.

    :param package_name: The name of the debugger support package.
    :param extras: Optional extras to add to the package requirement. Including square
        brackets. E.g. "[debugpy]".
    :return: The package requirement.
    """
    if IS_EDITABLE and REPO_ROOT is not None:
        local_path = REPO_ROOT / "debugger-support"
        if local_path.exists() and local_path.is_dir():
            return f"{local_path}{extras}"
    return f"{package_name}{extras}=={briefcase.__version__}"


class AppPathMappings(TypedDict):
    device_sys_path_regex: str
    device_subfolders: list[str]
    host_folders: list[str]


class AppPackagesPathMappings(TypedDict):
    sys_path_regex: str
    host_folder: str


class DebuggerConfig(TypedDict):
    debugger: str
    host: str
    port: int
    app_path_mappings: AppPathMappings | None
    app_packages_path_mappings: AppPackagesPathMappings | None


class DebuggerConnectionMode(str, enum.Enum):
    SERVER = "server"
    CLIENT = "client"


class BaseDebugger(ABC):
    """Definition for a plugin that defines a new Briefcase debugger."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name debugger."""

    @property
    @abstractmethod
    def connection_mode(self) -> DebuggerConnectionMode:
        """Return the connection mode of the debugger."""

    @property
    @abstractmethod
    def debugger_support_pkg(self) -> str:
        """Get the name of the debugger support package."""
