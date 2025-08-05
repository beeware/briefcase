from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from typing import TypedDict


class AppPathMappings(TypedDict):
    device_sys_path_regex: str
    device_subfolders: list[str]
    host_folders: list[str]


class AppPackagesPathMappings(TypedDict):
    sys_path_regex: str
    host_folder: str


class DebuggerConfig(TypedDict):
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
    def connection_mode(self) -> DebuggerConnectionMode:
        """Return the connection mode of the debugger."""

    @property
    @abstractmethod
    def debugger_support_pkg(self) -> str:
        """Get the name of the debugger support package."""
