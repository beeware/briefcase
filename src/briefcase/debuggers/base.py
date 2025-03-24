from __future__ import annotations

import dataclasses
import enum
from abc import ABC
from typing import ClassVar, TypedDict

from briefcase.console import Console
from briefcase.exceptions import BriefcaseCommandError, BriefcaseConfigError


class AppPathMappings(TypedDict):
    device_sys_path_regex: str
    device_subfolders: list[str]
    host_folders: list[str]


class AppPackagesPathMappings(TypedDict):
    sys_path_regex: str
    host_folder: str


class RemoteDebuggerConfig(TypedDict):
    debugger: str
    mode: str  # client / server
    ip: str
    port: int
    app_path_mappings: AppPathMappings | None
    app_packages_path_mappings: AppPackagesPathMappings | None


class DebuggerMode(str, enum.Enum):
    SERVER = "server"
    CLIENT = "client"


@dataclasses.dataclass
class DebuggerConfig:
    mode: str | None
    ip: str | None
    port: int | None


def parse_remote_debugger_cfg(
    remote_debugger_cfg: str,
) -> tuple[str, DebuggerConfig]:
    """
    Convert a remote debugger config string into a DebuggerConfig object.

    The config string is expected to be in the form:
        "[DEBUGGER[,[IP:]PORT][,MODE]]"

    Config examples:
        ""
        "pdb"
        "pdb,5678"
        "pdb,,server"
        "pdb,localhost:5678,server"
    """
    debugger = ip_and_port = ip = port = mode = None
    parts = remote_debugger_cfg.split(",")
    if len(parts) == 1:
        debugger = parts[0]
    elif len(parts) == 2:
        debugger, ip_and_port = parts
    elif len(parts) == 3:
        debugger, ip_and_port, mode = parts
    else:
        raise BriefcaseCommandError(
            f"Invalid remote debugger specification: {remote_debugger_cfg}"
        )

    if ip_and_port is not None:
        parts = ip_and_port.split(":")
        if len(parts) == 1:
            port = parts[0]
            if port == "":
                port = None
        elif len(parts) == 2:
            ip = parts[0]
            port = parts[1]
        else:
            raise BriefcaseCommandError(
                f"Invalid remote debugger specification: {remote_debugger_cfg}"
            )

    if port is not None:
        try:
            port = int(port)
        except ValueError:
            raise BriefcaseCommandError(f"Invalid remote debugger port: {port}")

    return debugger, DebuggerConfig(mode=mode, ip=ip, port=port)


class BaseDebugger(ABC):
    """Definition for a plugin that defines a new Briefcase debugger."""

    name: str
    supported_modes: ClassVar[list[DebuggerMode]]
    default_mode: ClassVar[DebuggerMode]
    default_ip: ClassVar[str] = "localhost"
    default_port: ClassVar[int] = 5678

    def __init__(self, console: Console, config: DebuggerConfig) -> None:
        self.console = console
        self.mode: DebuggerMode = DebuggerMode(config.mode or self.default_mode)
        self.ip: str = config.ip or self.default_ip
        self.port: int = config.port or self.default_port

        if self.mode not in self.supported_modes:
            raise BriefcaseConfigError(
                f"Unsupported debugger mode: {self.mode} for {self.__class__.__name__}"
            )

    @property
    def additional_requirements(self) -> list[str]:
        """Return a list of additional requirements for the debugger."""
        return []
