from __future__ import annotations

import os
import platform
import shutil
import sys
from abc import ABC
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import DefaultDict

import requests
from cookiecutter.main import cookiecutter

from briefcase.config import AppConfig
from briefcase.console import Console, Log
from briefcase.integrations.download import Download
from briefcase.integrations.subprocess import Subprocess


# TODO: Implement Tool base class
class Tool(ABC):
    """Tool Base."""  # pragma: no cover


class ToolCache(Mapping):
    platform = platform
    os = os
    shutil = shutil
    sys = sys

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

        # Built-in tools without any external dependencies
        Subprocess.verify(tools=self)
        Download.verify(tools=self)

    def __getitem__(self, app: AppConfig) -> ToolCache:
        return self.app_tools[app]

    def __iter__(self):
        return iter(self.app_tools)

    def __len__(self) -> int:
        return len(self.app_tools)

    def __bool__(self):
        # always True instead of __len__() != 0
        return True
