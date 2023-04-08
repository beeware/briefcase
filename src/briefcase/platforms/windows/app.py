import subprocess
from contextlib import suppress
from pathlib import Path

from briefcase.commands import BuildCommand, OpenCommand, PublishCommand, UpdateCommand
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.rcedit import RCEdit
from briefcase.integrations.windows_sdk import WindowsSDK
from briefcase.platforms.windows import (
    WindowsCreateCommand,
    WindowsMixin,
    WindowsPackageCommand,
    WindowsRunCommand,
)


class WindowsAppMixin(WindowsMixin):
    output_format = "app"
    packaging_root = Path("src")

    def project_path(self, app):
        return self.bundle_path(app)


class WindowsAppCreateCommand(WindowsAppMixin, WindowsCreateCommand):
    description = "Create and populate a Windows app."


class WindowsAppUpdateCommand(WindowsAppCreateCommand, UpdateCommand):
    description = "Update an existing Windows app."


class WindowsAppOpenCommand(WindowsAppMixin, OpenCommand):
    description = "Open the folder containing an existing Windows app."


class WindowsAppBuildCommand(WindowsAppMixin, BuildCommand):
    description = "Build a Windows app."

    def verify_tools(self):
        super().verify_tools()
        RCEdit.verify(tools=self.tools)
        # The Windows SDK is only needed if it has previously been used to sign
        # the binary and MSI; therefore, ignore if it isn't available since the
        # stub app should not have any signatures to remove in that case.
        with suppress(BriefcaseCommandError):
            WindowsSDK.verify(tools=self.tools)

    def build_app(self, app: BaseConfig, **kwargs):
        """Build the application.

        :param app: The config object for the app
        """
        self.logger.info("Building App...", prefix=app.app_name)

        if hasattr(self.tools, "windows_sdk"):
            # If an app has been packaged and code signed previously, then the digital
            # signature on the app binary needs to be removed before re-building the app.
            # It is not safe to use RCEdit on signed binaries since it corrupts them.
            with self.input.wait_bar(
                "Removing any digital signatures from stub app..."
            ):
                try:
                    self.tools.subprocess.check_output(
                        [
                            self.tools.windows_sdk.signtool_exe,
                            "remove",
                            "-s",
                            self.binary_path(app).relative_to(self.bundle_path(app)),
                        ],
                        cwd=self.bundle_path(app),
                    )
                except subprocess.CalledProcessError as e:
                    # Ignore this error from signtool since it is logged if the file
                    # is not currently signed
                    if "error: 0x00000057" not in e.stdout:
                        raise BriefcaseCommandError(
                            f"""\
Failed to remove any existing digital signatures from the stub app.

Recreating the app layout may also help resolve this issue:

    $ briefcase create {self.platform} {self.output_format}

"""
                        ) from e

        with self.input.wait_bar("Setting stub app details..."):
            try:
                self.tools.subprocess.run(
                    [
                        self.tools.rcedit.rcedit_path,
                        self.binary_path(app).relative_to(self.bundle_path(app)),
                        "--set-version-string",
                        "CompanyName",
                        app.author,
                        # Although "FileDescription" sounds like it should be a... description,
                        # this is the label that appears as a grouping in the Task Manager
                        # when the application runs.
                        "--set-version-string",
                        "FileDescription",
                        app.formal_name,
                        "--set-version-string",
                        "FileVersion",
                        app.version,
                        "--set-version-string",
                        "InternalName",
                        app.module_name,
                        "--set-version-string",
                        "OriginalFilename",
                        self.binary_path(app).name,
                        "--set-version-string",
                        "ProductName",
                        app.formal_name,
                        "--set-version-string",
                        "ProductVersion",
                        app.version,
                        "--set-icon",
                        "icon.ico",
                    ],
                    check=True,
                    cwd=self.bundle_path(app),
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to update details on stub app for {app.app_name}."
                ) from e


class WindowsAppRunCommand(WindowsAppMixin, WindowsRunCommand):
    description = "Run a Windows app."


class WindowsAppPackageCommand(WindowsAppMixin, WindowsPackageCommand):
    description = "Package a Windows app as an MSI."


class WindowsAppPublishCommand(WindowsAppMixin, PublishCommand):
    description = "Publish a Windows app."


# Declare the briefcase command bindings
create = WindowsAppCreateCommand
update = WindowsAppUpdateCommand
open = WindowsAppOpenCommand
build = WindowsAppBuildCommand
run = WindowsAppRunCommand
package = WindowsAppPackageCommand
publish = WindowsAppPublishCommand
