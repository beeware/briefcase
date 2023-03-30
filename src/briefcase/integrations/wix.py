import os
import shutil
from pathlib import Path

from briefcase.exceptions import (
    BriefcaseCommandError,
    MissingToolError,
    NonManagedToolError,
)
from briefcase.integrations.base import Tool, ToolCache

WIX_DOWNLOAD_URL = "https://github.com/wixtoolset/wix3/releases/download/wix3112rtm/wix311-binaries.zip"


class WiX(Tool):
    name = "wix"
    full_name = "WiX"

    def __init__(self, tools: ToolCache, wix_home: Path = None, bin_install=False):
        """Create a wrapper around a WiX install.

        :param tools: ToolCache of available tools.
        :param wix_home: The path of the WiX installation.
        :param bin_install: Is the install a binaries-only install? A full
            MSI install of WiX has a `/bin` folder in the paths; a
            binaries-only install does not.
        :returns: A valid WiX SDK wrapper. If WiX is not available, and was
            not installed, raises MissingToolError.
        """
        self.tools = tools
        if wix_home:
            self.wix_home = wix_home
        else:
            self.wix_home = tools.base_path / "wix"
        self.bin_install = bin_install

    @property
    def heat_exe(self):
        if self.bin_install:
            return self.wix_home / "heat.exe"
        else:
            return self.wix_home / "bin" / "heat.exe"

    @property
    def light_exe(self):
        if self.bin_install:
            return self.wix_home / "light.exe"
        else:
            return self.wix_home / "bin" / "light.exe"

    @property
    def candle_exe(self):
        if self.bin_install:
            return self.wix_home / "candle.exe"
        else:
            return self.wix_home / "bin" / "candle.exe"

    @classmethod
    def verify(cls, tools: ToolCache, install=True):
        """Verify that there is a WiX install available.

        If the WIX environment variable is set, that location will be checked
        for a valid WiX installation.

        If the location provided doesn't contain an SDK, or no location is provided,
        an SDK is downloaded.

        :param tools: ToolCache of available tools
        :param install: Should WiX be installed if it is not found?
        """
        # short circuit since already verified and available
        if hasattr(tools, "wix"):
            return tools.wix

        # Look for the WIX environment variable
        wix_env = tools.os.environ.get("WIX")
        if wix_env:
            wix_home = Path(wix_env)

            # Set up the paths for the WiX executables we will use.
            wix = WiX(tools=tools, wix_home=wix_home)

            if not wix.exists():
                raise BriefcaseCommandError(
                    f"""\
The WIX environment variable:

{wix_home}

does not point to an install of the WiX Toolset.
"""
                )

        else:
            wix = WiX(tools=tools, bin_install=True)

            if not wix.exists():
                if install:
                    tools.logger.info(
                        "The WiX toolset was not found; downloading and installing...",
                        prefix=cls.name,
                    )
                    wix.install()
                else:
                    raise MissingToolError("WiX")

        tools.wix = wix
        return wix

    def exists(self):
        return (
            self.heat_exe.is_file()
            and self.light_exe.is_file()
            and self.candle_exe.is_file()
        )

    @property
    def managed_install(self):
        try:
            # Determine if wix_home is relative to the briefcase data directory.
            # If wix_home isn't inside this directory, this will raise a ValueError,
            # indicating it is a non-managed install.
            self.wix_home.relative_to(self.tools.base_path)
            return True
        except ValueError:
            return False

    def install(self):
        """Download and install WiX."""
        wix_zip_path = self.tools.download.file(
            url=WIX_DOWNLOAD_URL,
            download_path=self.tools.base_path,
            role="WiX",
        )

        try:
            with self.tools.input.wait_bar("Installing WiX..."):
                # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
                self.tools.shutil.unpack_archive(
                    os.fsdecode(wix_zip_path),
                    extract_dir=os.fsdecode(self.wix_home),
                )
        except (shutil.ReadError, EOFError) as e:
            raise BriefcaseCommandError(
                f"""\
Unable to unpack WiX ZIP file. The download may have been
interrupted or corrupted.

Delete {wix_zip_path} and run briefcase again.
"""
            ) from e

        # Zip file no longer needed once unpacked.
        wix_zip_path.unlink()

    def uninstall(self):
        """Uninstall WiX."""
        with self.tools.input.wait_bar("Removing old WiX install..."):
            self.tools.shutil.rmtree(self.wix_home)

    def upgrade(self):
        """Upgrade an existing WiX install."""
        if not self.managed_install:
            raise NonManagedToolError("WiX")
        if not self.exists():
            raise MissingToolError("WiX")

        self.uninstall()
        self.install()
