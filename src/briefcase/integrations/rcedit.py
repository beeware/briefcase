from __future__ import annotations

from pathlib import Path

from briefcase.exceptions import MissingToolError
from briefcase.integrations.base import ManagedTool, ToolCache


class RCEdit(ManagedTool):
    name = "rcedit"
    full_name = "RCEdit"
    supported_host_os = {"Windows"}

    @property
    def download_url(self) -> str:
        return (
            "https://github.com/electron/rcedit/releases/download/v2.0.0/rcedit-x64.exe"
        )

    @property
    def rcedit_path(self) -> Path:
        return self.tools.base_path / "rcedit-x64.exe"

    @classmethod
    def verify_install(cls, tools: ToolCache, install: bool = True, **kwargs) -> RCEdit:
        """Verify that rcedit is available.

        :param tools: ToolCache of available tools
        :param install: Should the tool be installed if it is not found?
        :returns: A valid rcedit tool wrapper. If rcedit is not available, and was not
            installed, raises MissingToolError.
        """
        # short circuit since already verified and available
        if hasattr(tools, "rcedit"):
            return tools.rcedit

        rcedit = RCEdit(tools=tools)

        if not rcedit.exists():
            if install:
                tools.logger.info(
                    "RCEdit was not found; downloading and installing...",
                    prefix=cls.name,
                )
                rcedit.install()
            else:
                raise MissingToolError("RCEdit")

        tools.rcedit = rcedit
        return rcedit

    def exists(self) -> bool:
        return self.rcedit_path.exists()

    def install(self):
        """Download and install RCEdit."""
        self.tools.file.download(
            url=self.download_url,
            download_path=self.tools.base_path,
            role="RCEdit",
        )

    def uninstall(self):
        """Uninstall RCEdit."""
        with self.tools.input.wait_bar("Removing old RCEdit install..."):
            self.rcedit_path.unlink()
