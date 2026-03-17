from __future__ import annotations

import subprocess
from pathlib import Path

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.formats.base import BasePackagingFormat, WindowsPackageCommandAPI


class WindowsMSIPackagingFormat(BasePackagingFormat):
    command: WindowsPackageCommandAPI

    @property
    def name(self) -> str:
        return "msi"

    def distribution_path(self, app: AppConfig) -> Path:
        return self.command.dist_path / f"{app.formal_name}-{app.version}.msi"

    def package_app(
        self,
        app: AppConfig,
        identity: str | None = None,
        adhoc_sign: bool = False,
        file_digest: str = "sha256",
        use_local_machine: bool = False,
        cert_store: str = "My",
        timestamp_url: str = "http://timestamp.digicert.com",
        timestamp_digest: str = "sha256",
        **kwargs,
    ):
        """Package a Windows app as an MSI installer."""
        if adhoc_sign:
            sign_app = False
        elif identity:
            sign_app = True
        else:
            sign_app = False
            self.command.console.warning("""
*************************************************************************
** WARNING: No signing identity provided                               **
*************************************************************************

    Briefcase will not sign the app. To provide a signing identity,
    use the `--identity` option; or, to explicitly disable signing,
    use `--adhoc-sign`.

*************************************************************************
""")

        if sign_app:
            self.command.console.info("Signing App...", prefix=app.app_name)
            sign_options = {
                "identity": identity,
                "file_digest": file_digest,
                "use_local_machine": use_local_machine,
                "cert_store": cert_store,
                "timestamp_url": timestamp_url,
                "timestamp_digest": timestamp_digest,
            }
            self.command.sign_file(
                app=app, filepath=self.command.binary_path(app), **sign_options
            )

        dist_path = self.distribution_path(app)
        try:
            with self.command.console.wait_bar("Building MSI..."):
                self.command.tools.subprocess.run(
                    [
                        self.command.tools.wix.wix_exe,
                        "build",
                        "-ext",
                        self.command.tools.wix.ext_path("UI"),
                        "-arch",
                        "x64",  # Default is x86, regardless of the build machine.
                        f"{app.app_name}.wxs",
                        "-loc",
                        "unicode.wxl",
                        "-pdbtype",
                        "none",
                        "-o",
                        dist_path,
                    ],
                    check=True,
                    cwd=self.command.bundle_path(app),
                )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Unable to package app {app.app_name}.") from e

        if sign_app:
            self.command.console.info("Signing MSI...", prefix=app.app_name)
            self.command.sign_file(
                app=app,
                filepath=dist_path,
                **sign_options,
            )

    def priority(self, app: AppConfig) -> int:
        # MSI is the default for Windows apps
        return 10
