from __future__ import annotations

import os
import platform
import shutil
import sys
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, DefaultDict

import requests
from cookiecutter.main import cookiecutter

from briefcase.config import AppConfig
from briefcase.console import Console, Log
from briefcase.exceptions import MissingToolError, NonManagedToolError

if TYPE_CHECKING:
    # Tools are imported only for type checking
    # to avoid circular import errors.
    import git as git_

    from briefcase.integrations.android_sdk import AndroidSDK
    from briefcase.integrations.docker import Docker, DockerAppContext
    from briefcase.integrations.download import Download
    from briefcase.integrations.flatpak import Flatpak
    from briefcase.integrations.java import JDK
    from briefcase.integrations.linuxdeploy import LinuxDeploy
    from briefcase.integrations.rcedit import RCEdit
    from briefcase.integrations.subprocess import Subprocess
    from briefcase.integrations.visualstudio import VisualStudio
    from briefcase.integrations.windows_sdk import WindowsSDK
    from briefcase.integrations.wix import WiX
    from briefcase.integrations.xcode import Xcode, XcodeCliTools


# Registry of all defined Tools
tool_registry: dict[str, type[Tool]] = dict()


class Tool(ABC):
    """Tool Base."""

    name: str
    full_name: str

    def __init__(self, tools: ToolCache, **kwargs):
        self.tools = tools

    def __init_subclass__(tool, **kwargs):
        """Register each tool at definition."""
        try:
            tool_registry[tool.name] = tool
        except AttributeError:
            tool_registry[tool.__name__] = tool

    @classmethod
    @abstractmethod
    def verify(cls, tools: ToolCache, **kwargs):
        """Confirm the tool is available and usable on the host platform."""
        ...

    def exists(self) -> bool:
        """Is the tool currently installed?"""
        raise NotImplementedError(
            f"Missing implementation for Tool {self.__class__.__name__!r}"
        )

    @property
    def managed_install(self) -> bool:
        """Is Briefcase managing the installation of this tool?"""
        return False

    def install(self, *a, **kw):
        """Install the tool as managed by Briefcase."""
        if self.managed_install:
            raise NotImplementedError(
                f"Missing implementation for Tool {self.__class__.__name__!r}"
            )
        else:
            raise NonManagedToolError(self.full_name)

    def uninstall(self, *a, **kw):
        """Uninstall the tool."""
        if self.managed_install:
            raise NotImplementedError(
                f"Missing implementation for Tool {self.__class__.__name__!r}"
            )
        else:
            raise NonManagedToolError(self.full_name)

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
    download: Download
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
        home_path: Path = None,
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

        self.app_tools: DefaultDict[AppConfig, ToolCache] = defaultdict(
            lambda: ToolCache(
                logger=self.logger,
                console=self.input,
                base_path=self.base_path,
                home_path=self.home_path,
            )
        )

    def __getitem__(self, app: AppConfig) -> ToolCache:
        return self.app_tools[app]

    def __iter__(self):
        return iter(self.app_tools)

    def __len__(self) -> int:
        return len(self.app_tools)

    def __bool__(self):
        # always True instead of __len__() != 0
        return True
