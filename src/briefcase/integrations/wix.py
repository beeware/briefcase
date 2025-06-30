from __future__ import annotations

import re
from pathlib import Path
from subprocess import CalledProcessError

from packaging.version import Version

from briefcase.exceptions import BriefcaseCommandError, MissingToolError
from briefcase.integrations.base import ManagedTool, ToolCache


class WiX(ManagedTool):
    name = "wix"
    full_name = "WiX"
    supported_host_os = {"Windows"}

    # WARNING: version 6 and later have licensing issues: see
    # https://github.com/beeware/briefcase/issues/1185.
    version = Version("5.0.2")

    def __init__(self, tools: ToolCache, wix_home: Path | None = None):
        """Create a wrapper around a WiX install.

        :param tools: ToolCache of available tools.
        :param wix_home: The path of the WiX installation.
        """
        super().__init__(tools=tools)
        if wix_home:
            self.wix_home = wix_home
        else:
            self.wix_home = tools.base_path / "wix"

    @property
    def download_url(self) -> str:
        return (
            f"https://github.com/wixtoolset/wix/releases/download/v{self.version}/"
            f"wix-cli-x64.msi"
        )

    @property
    def wix_exe(self) -> Path:
        return (
            self.wix_home
            / f"PFiles64/WiX Toolset v{self.version.major}.{self.version.minor}/bin"
            / "wix.exe"
        )

    def ext_path(self, name: str) -> Path:
        return (
            self.wix_home
            / f"CFiles64/WixToolset/extensions/WixToolset.{name}.wixext/{self.version}"
            / f"wixext{self.version.major}/WixToolset.{name}.wixext.dll"
        )

    @classmethod
    def verify_install(cls, tools: ToolCache, install: bool = True, **kwargs) -> WiX:
        """Verify that there is a WiX install available.

        WiX is a small tool, and there's a close relationship between the WiX version
        and the template syntax, so we always use a Briefcase-managed copy, and upgrade
        it automatically.

        :param tools: ToolCache of available tools
        :param install: Should WiX be installed if it is not found?
        """
        # short circuit since already verified and available
        if hasattr(tools, "wix"):
            return tools.wix

        wix = WiX(tools)
        if not wix.exists():
            if install:
                tools.console.info(
                    "The WiX toolset was not found; downloading and installing...",
                    prefix=cls.name,
                )
                wix.install()
            else:
                raise MissingToolError("WiX")
        else:
            try:
                # The string returned by --version may include "+" followed by a
                # commit ID; ignore this.
                installed_version = re.sub(
                    r"\+.*",
                    "",
                    tools.subprocess.check_output([wix.wix_exe, "--version"]),
                ).strip()
            except (OSError, CalledProcessError) as e:
                installed_version = None
                tools.console.error(
                    f"The WiX toolset is unusable ({type(e).__name__}: {e})"
                )

            if installed_version != str(wix.version):
                if installed_version is not None:
                    tools.console.info(
                        f"The WiX toolset is an unsupported version ({installed_version})"
                    )
                if install:
                    wix.upgrade()
                else:
                    raise MissingToolError("WiX")

        tools.console.debug(f"Using WiX at {wix.wix_home}")
        tools.wix = wix
        return wix

    def exists(self) -> bool:
        return self.wix_exe.is_file()

    @property
    def managed_install(self) -> bool:
        return True

    def install(self):
        """Download and install WiX."""
        wix_msi_path = self.tools.file.download(
            url=self.download_url,
            download_path=self.tools.base_path,
            role="WiX",
        )

        try:
            with self.tools.console.wait_bar("Installing WiX..."):
                self.tools.subprocess.run(
                    [
                        "msiexec",
                        "/a",  # Unpack the MSI into individual files
                        wix_msi_path,
                        "/qn",  # Disable GUI interaction
                        f"TARGETDIR={self.wix_home}",
                    ],
                    check=True,
                )
        except CalledProcessError as e:
            raise BriefcaseCommandError(
                f"""\
Unable to unpack WiX MSI file. The download may have been
interrupted or corrupted.

Delete {wix_msi_path} and run briefcase again.
"""
            ) from e

        wix_msi_path.unlink()

    def uninstall(self):
        """Uninstall WiX."""
        with self.tools.console.wait_bar("Removing old WiX install..."):
            self.tools.shutil.rmtree(self.wix_home)
