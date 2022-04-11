import os
import shutil
from pathlib import Path

from requests import exceptions as requests_exceptions

from briefcase.exceptions import (
    BriefcaseCommandError,
    MissingToolError,
    NetworkFailure,
    NonManagedToolError
)

WIX_DOWNLOAD_URL = "https://github.com/wixtoolset/wix3/releases/download/wix3112rtm/wix311-binaries.zip"


class WiX:
    name = 'wix'
    full_name = 'WiX'

    def __init__(self, command, wix_home=None, bin_install=False):
        """
        Create a wrapper around a WiX install.

        :param command: The command using the wrapper.
        :param wix_home: The path of the WiX installation.
        :param bin_install: Is the install a binaries-only install? A full
            MSI install of WiX has a `/bin` folder in the paths; a
            binaries-only install does not.
        """
        self.command = command
        if wix_home:
            self.wix_home = wix_home
        else:
            self.wix_home = command.tools_path / 'wix'
        self.bin_install = bin_install

    @property
    def heat_exe(self):
        if self.bin_install:
            return self.wix_home / 'heat.exe'
        else:
            return self.wix_home / 'bin' / 'heat.exe'

    @property
    def light_exe(self):
        if self.bin_install:
            return self.wix_home / 'light.exe'
        else:
            return self.wix_home / 'bin' / 'light.exe'

    @property
    def candle_exe(self):
        if self.bin_install:
            return self.wix_home / 'candle.exe'
        else:
            return self.wix_home / 'bin' / 'candle.exe'

    @classmethod
    def verify(cls, command, install=True):
        """
        Verify that there is a WiX install available.

        If the WIX environment variable is set, that location will be checked
        for a valid WiX installation.

        If the location provided doesn't contain an SDK, or no location is provided,
        an SDK is downloaded.

        :param command: The command making the verification request.
        :param install: Should WiX be installed if it is not found?
        :returns: A valid WiX SDK wrapper. If WiX is not available, and was
            not installed, raises MissingToolError.
        """
        if command.host_os != 'Windows':
            raise BriefcaseCommandError("""
A Windows MSI installer can only be created on Windows.
""")

        # Look for the WIX environment variable
        wix_env = command.os.environ.get("WIX")
        if wix_env:
            wix_home = Path(wix_env)

            # Set up the paths for the WiX executables we will use.
            wix = WiX(command=command, wix_home=wix_home)

            if not wix.exists():
                raise BriefcaseCommandError("""
The WIX environment variable does not point to an install of the
WiX Toolset. Current value: {wix_home!r}
""".format(wix_home=wix_home))

        else:
            wix = WiX(command=command, bin_install=True)

            if not wix.exists():
                if install:
                    wix.install()
                else:
                    raise MissingToolError('WiX')

        return wix

    def exists(self):
        return (
            self.heat_exe.exists()
            and self.light_exe.exists()
            and self.candle_exe.exists()
        )

    @property
    def managed_install(self):
        try:
            # Determine if wix_home is relative to the .briefcase folder.
            # If wix_home isn't inside .briefcase, this will raise a ValueError,
            # indicating it is a non-managed install.
            self.wix_home.relative_to(self.command.tools_path)
            return True
        except ValueError:
            return False

    def install(self):
        """
        Download and install WiX.
        """
        try:
            wix_zip_path = self.command.download_url(
                url=WIX_DOWNLOAD_URL,
                download_path=self.command.tools_path,
            )
        except requests_exceptions.ConnectionError:
            raise NetworkFailure("download WiX")

        try:
            print("Installing WiX...")
            # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
            self.command.shutil.unpack_archive(
                os.fsdecode(wix_zip_path),
                extract_dir=os.fsdecode(self.wix_home)
            )
        except (shutil.ReadError, EOFError):
            raise BriefcaseCommandError("""
Unable to unpack WiX ZIP file. The download may have been
interrupted or corrupted.

Delete {wix_zip_path} and run briefcase again.""".format(
                    wix_zip_path=wix_zip_path
                )
            )

        # Zip file no longer needed once unpacked.
        wix_zip_path.unlink()

    def upgrade(self):
        """
        Upgrade an existing WiX install.
        """
        if self.managed_install:
            if self.exists():
                print("Removing old WiX install...")
                self.command.shutil.rmtree(self.wix_home)

                self.install()
                print("...done.")
            else:
                raise MissingToolError('WiX')
        else:
            raise NonManagedToolError('WiX')
