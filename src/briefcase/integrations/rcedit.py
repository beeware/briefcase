from requests import exceptions as requests_exceptions

from briefcase.exceptions import MissingToolError, NetworkFailure


class RCEdit:
    name = "rcedit"

    def __init__(self, command):
        self.command = command

    @property
    def download_url(self):
        return (
            "https://github.com/electron/rcedit/releases/download/v1.1.1/rcedit-x64.exe"
        )

    @property
    def rcedit_path(self):
        return self.command.tools_path / "rcedit-x64.exe"

    @classmethod
    def verify(cls, command, install=True):
        """Verify that rcedit is available.

        :param command: The command that needs to use rcedit
        :param install: Should the tool be installed if it is not found?
        :returns: A valid rcedit tool wrapper. If rcedit is not
            available, and was not installed, raises MissingToolError.
        """
        rcedit = RCEdit(command)

        if not rcedit.exists():
            if install:
                command.logger.info(
                    "RCEdit was not found; downloading and installing...",
                    prefix=cls.name,
                )
                rcedit.install()
            else:
                raise MissingToolError("RCEdit")

        return RCEdit(command)

    def exists(self):
        return self.rcedit_path.exists()

    @property
    def managed_install(self):
        return True

    def install(self):
        """Download and install RCEdit."""
        try:
            self.command.download_url(
                url=self.download_url, download_path=self.command.tools_path
            )
        except requests_exceptions.ConnectionError as e:
            raise NetworkFailure("downloading RCEdit") from e

    def uninstall(self):
        """Uninstall RCEdit."""
        with self.command.input.wait_bar("Removing old RCEdit install..."):
            self.rcedit_path.unlink()

    def upgrade(self):
        """Upgrade an existing RCEdit install."""
        if not self.exists():
            raise MissingToolError("RCEdit")

        self.uninstall()
        self.install()
