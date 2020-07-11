import shutil
from pathlib import Path

from requests import exceptions as requests_exceptions

from briefcase.exceptions import (
    BriefcaseCommandError,
    NetworkFailure
)


WIX_DOWNLOAD_URL = "https://github.com/wixtoolset/wix3/releases/download/wix3112rtm/wix311-binaries.zip"

class WiX:
    def __init__(self, wix_home, bin_install=False):
        """
        Create a wrapper around a WiX install.

        :param wix_home: The path of the WiX installation.
        :param bin_install: Is the install a binaries-only install? A full
            MSI install of WiX has a `/bin` folder in the paths; a
            binaries-only install does not.
        """
        self.wix_home = wix_home
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

    def exists(self):
        return (
            self.heat_exe.exists()
            and self.light_exe.exists()
            and self.candle_exe.exists()
        )


def verify_wix(command):
    """
    Verify that there is a WiX install available.

    If the WIX environment variable is set, that location will be checked
    for a valid WiX installation.

    If the location provided doesn't contain an SDK, or no location is provided,
    an SDK is downloaded.

    :param command: The command making the verification request.
    :returns: A triple containing the paths to the heat, light, and candle
        executables.
    """
    if command.host_os != 'Windows':
        raise BriefcaseCommandError("""
A Windows MSI installer can only be created on Windows.
""")

    # Look for the WIX environment variable
    wix_env = command.os.environ.get("WIX")
    if wix_env:
        wix_path = Path(wix_env)

        # Set up the paths for the WiX executables we will use.
        wix = WiX(wix_path)

        if not wix.exists():
            raise BriefcaseCommandError("""
The WIX environment variable does not point to an install of the
WiX Toolset. Current value: {wix_path!r}
""".format(wix_path=wix_path))

    else:
        wix_path = command.dot_briefcase_path / 'tools' / 'wix'
        wix = WiX(wix_path, bin_install=True)

        if not wix.exists():
            print("Downloading WiX...")
            try:
                wix_zip_path = command.download_url(
                    url=WIX_DOWNLOAD_URL,
                    download_path=command.dot_briefcase_path / "tools",
                )
            except requests_exceptions.ConnectionError:
                raise NetworkFailure("download WiX")

            try:
                command.shutil.unpack_archive(
                    str(wix_zip_path),
                    extract_dir=str(wix_path)
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

    return wix
