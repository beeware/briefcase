from __future__ import annotations

import os
import platform
import shutil
import sys
from abc import ABC
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, DefaultDict

import requests
from cookiecutter.main import cookiecutter

from briefcase.config import AppConfig
from briefcase.console import Console, Log

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


# TODO: Implement Tool base class
class Tool(ABC):
    """Tool Base."""  # pragma: no cover


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
    xcode: bool
    xcode_cli: bool

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
