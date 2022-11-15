from briefcase.exceptions import MissingToolError
from briefcase.integrations.base import Tool, ToolCache


class RCEdit(Tool):
    name = "rcedit"
    full_name = "RCEdit"

    def __init__(self, tools: ToolCache):
        self.tools = tools

    @property
    def download_url(self):
        return (
            "https://github.com/electron/rcedit/releases/download/v1.1.1/rcedit-x64.exe"
        )

    @property
    def rcedit_path(self):
        return self.tools.base_path / "rcedit-x64.exe"

    @classmethod
    def verify(cls, tools: ToolCache, install=True):
        """Verify that rcedit is available.

        :param tools: ToolCache of available tools
        :param install: Should the tool be installed if it is not found?
        :returns: A valid rcedit tool wrapper. If rcedit is not
            available, and was not installed, raises MissingToolError.
        """
        # short circuit since already verified and available
        if hasattr(tools, "rcedit"):
            return tools.rcedit

        rcedit = RCEdit(tools)

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

    def exists(self):
        return self.rcedit_path.exists()

    @property
    def managed_install(self):
        return True

    def install(self):
        """Download and install RCEdit."""
        self.tools.download.file(
            url=self.download_url,
            download_path=self.tools.base_path,
            role="RCEdit",
        )

    def uninstall(self):
        """Uninstall RCEdit."""
        with self.tools.input.wait_bar("Removing old RCEdit install..."):
            self.rcedit_path.unlink()

    def upgrade(self):
        """Upgrade an existing RCEdit install."""
        if not self.exists():
            raise MissingToolError("RCEdit")

        self.uninstall()
        self.install()
