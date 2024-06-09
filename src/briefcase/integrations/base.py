from __future__ import annotations

import locale
import os
import platform
import shutil
import sys
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Mapping
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, DefaultDict, TypeVar

import requests
from cookiecutter.main import cookiecutter

from briefcase.config import AppConfig
from briefcase.console import Console, Log
from briefcase.exceptions import (
    MissingToolError,
    NonManagedToolError,
    UnsupportedHostError,
)

if TYPE_CHECKING:
    # Tools are imported only for type checking
    # to avoid circular import errors.
    import git as git_

    from briefcase.integrations.android_sdk import AndroidSDK
    from briefcase.integrations.docker import Docker, DockerAppContext
    from briefcase.integrations.file import File
    from briefcase.integrations.flatpak import Flatpak
    from briefcase.integrations.java import JDK
    from briefcase.integrations.linuxdeploy import LinuxDeploy
    from briefcase.integrations.rcedit import RCEdit
    from briefcase.integrations.subprocess import Subprocess
    from briefcase.integrations.visualstudio import VisualStudio
    from briefcase.integrations.windows_sdk import WindowsSDK
    from briefcase.integrations.wix import WiX
    from briefcase.integrations.xcode import Xcode, XcodeCliTools

ToolT = TypeVar("ToolT", bound="Tool")
ManagedToolT = TypeVar("ManagedToolT", bound="ManagedTool")

# Registry of all defined Tools
tool_registry: dict[str, type[Tool | ManagedTool]] = dict()

DEFAULT_SYSTEM_ENCODING = "UTF-8"


class Tool(ABC):
    """Tool Base."""

    name: str
    full_name: str
    supported_host_os: set[str] = {"Darwin", "Linux", "Windows"}

    def __init__(self, tools: ToolCache, **kwargs):
        self.tools = tools

    def __init_subclass__(cls, **kwargs):
        """Register each tool when it is defined."""
        if cls.name != "managed_tool_base":
            tool_registry[cls.name] = cls

    @classmethod
    def verify(
        cls: type[ToolT],
        tools: ToolCache,
        app: AppConfig | None = None,
        **kwargs,
    ) -> ToolT:
        """Confirm the tool is available and usable on the host platform."""
        cls.verify_host(tools=tools)
        tool = cls.verify_install(tools=tools, app=app, **kwargs)
        return tool

    @classmethod
    def verify_host(cls, tools: ToolCache):
        """Confirm the tool is supported on the platform."""
        if tools.host_os not in cls.supported_host_os:
            raise UnsupportedHostError(
                f"{cls.name} is not supported on {tools.host_os}"
            )

    @classmethod
    @abstractmethod
    def verify_install(cls: type[ToolT], tools: ToolCache, **kwargs) -> ToolT:
        """Confirm the tool is installed and available."""

    @property
    def managed_install(self) -> bool:
        """Is Briefcase managing the installation of this tool?"""
        return False


class ManagedTool(Tool):
    """Tool that can be managed by Briefcase."""

    name = "managed_tool_base"

    @classmethod
    def verify(
        cls: type[ManagedToolT],
        tools: ToolCache,
        app: AppConfig | None = None,
        install: bool = True,
        **kwargs,
    ) -> ManagedToolT:
        """Confirm the managed tool is installed and available."""
        return super().verify(tools=tools, app=app, install=install, **kwargs)

    @abstractmethod
    def exists(self) -> bool:
        """Is the tool currently installed?"""

    @abstractmethod
    def install(self):
        """Install the tool as managed by Briefcase."""

    @abstractmethod
    def uninstall(self):
        """Uninstall a Briefcase managed tool."""

    @property
    def managed_install(self) -> bool:
        """Is Briefcase managing the installation of this tool?"""
        return True

    def upgrade(self):
        """Upgrade a managed tool."""
        if self.managed_install:
            if not self.exists():
                raise MissingToolError(self.full_name)
            self.uninstall()
            self.install()
        else:
            raise NonManagedToolError(self.full_name)


class ToolCache(Mapping):
    # Useful fixed filesystem locations
    ETC_OS_RELEASE: Path = Path("/etc/os-release")

    # Briefcase tools
    android_sdk: AndroidSDK
    app_context: Subprocess | DockerAppContext
    docker: Docker
    file: File
    flatpak: Flatpak
    git: git_
    java: JDK
    linuxdeploy: LinuxDeploy
    rcedit: RCEdit
    subprocess: Subprocess
    visualstudio: VisualStudio
    windows_sdk: WindowsSDK
    wix: WiX
    xcode: Xcode
    xcode_cli: XcodeCliTools

    # Python stdlib tools
    platform = platform
    os = os
    shutil = shutil
    sys = sys

    # Third party tools
    cookiecutter = staticmethod(cookiecutter)
    requests = requests

    def __init__(
        self,
        logger: Log,
        console: Console,
        base_path: Path,
        home_path: Path | None = None,
    ):
        """Cache for managing tool access and verification.

        Non-app-specific tools are available via attribute access:
            e.g.: tools.subprocess
        App-specific tools are available via dictionary access:
            e.g.: tools[app].app_context

        :param logger: Logger for console and logfile.
        :param console: Facilitates console interaction and input solicitation.
        :param base_path: Base directory for tools (e.g. ~/.cache/briefcase/tools).
        :param home_path: Home directory for current user.
        """
        self.logger = logger
        self.input = console
        self.base_path = Path(base_path)
        self.home_path = Path(
            os.path.expanduser(home_path if home_path else Path.home())
        )

        self.host_arch = self.platform.machine()
        self.host_os = self.platform.system()
        # Python is 32bit if its pointers can only address with 32 bits or fewer
        self.is_32bit_python = self.sys.maxsize <= 2**32

        self.app_tools: DefaultDict[AppConfig, ToolCache] = defaultdict(
            lambda: ToolCache(
                logger=self.logger,
                console=self.input,
                base_path=self.base_path,
                home_path=self.home_path,
            )
        )

    @cached_property
    def system_encoding(self) -> str:
        """The character encoding for the system's locale.

        This locale API tries to determine the system's default encoding and generally
        works on typically configured systems; although, there are potential pitfalls
        in certain situations...so, this is best-effort.

        This API is used over getpreferredencoding() to avoid respecting Python's UTF-8
        mode; the system may not be using UTF-8 even if Python is configured to use it.

        :returns: a character encoding (upper-cased), e.g. UTF-8. Defaults to UTF-8.
        """
        if sys.version_info < (3, 11):  # pragma: no-cover-if-gte-py311
            encoding = locale.getdefaultlocale()[1]  # deprecated in Python 3.11
        else:  # pragma: no-cover-if-lt-py311
            encoding = locale.getencoding()

        if not encoding:
            encoding = DEFAULT_SYSTEM_ENCODING

        return encoding.upper()

    def __getitem__(self, app: AppConfig) -> ToolCache:
        return self.app_tools[app]

    def __iter__(self):
        return iter(self.app_tools)

    def __len__(self) -> int:
        return len(self.app_tools)

    def __bool__(self):
        # always True instead of __len__() != 0
        return True
