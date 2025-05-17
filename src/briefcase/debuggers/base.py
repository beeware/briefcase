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


class DebuggerMode(str, enum.Enum):
    SERVER = "server"
    CLIENT = "client"


# @dataclasses.dataclass
# class DebuggerOptions:
#     mode: str
#     host: str
#     port: int


class BaseDebugger(ABC):
    """Definition for a plugin that defines a new Briefcase debugger."""

    name: str

    @property
    @abstractmethod
    def additional_requirements(self) -> list[str]:
        """Return a list of additional requirements for the debugger."""
        raise NotImplementedError

    @property
    @abstractmethod
    def debugger_mode(self) -> DebuggerMode:
        """Return the mode of the debugger."""
        raise NotImplementedError

    # def validate_run_options(self, mode: str | None, host: str | None, port: int | None) -> DebuggerOptions:
    #     """Validate the run options for the debugger."""
    #     if mode is None:
    #         mode = self.default_mode.value
    #     elif mode not in [m.value for m in self.supported_modes]:
    #         raise BriefcaseCommandError(
    #             f"Invalid mode '{mode}'. Supported modes are: {', '.join([m.value for m in self.supported_modes])}."
    #         )

    #     if host is None:
    #         host = self.default_host

    #     if port is None:
    #         port = self.default_port

    #     return DebuggerOptions(mode=mode, host=host, port=port)

    # @abstractmethod
    # def get_env(self) -> dict[str, str]:
    #     """Return environment variables to set before running the debugger."""
    #     return {}
