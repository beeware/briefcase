import subprocess
from pathlib import Path

from briefcase.commands import BuildCommand, OpenCommand, PublishCommand, UpdateCommand
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.visualstudio import VisualStudio
from briefcase.platforms.windows import (
    WindowsCreateCommand,
    WindowsMixin,
    WindowsPackageCommand,
    WindowsRunCommand,
)


class WindowsVisualStudioMixin(WindowsMixin):
    output_format = "VisualStudio"
    packaging_root = Path("x64") / "Release"

    def project_path(self, app):
        return self.bundle_path(app) / f"{app.formal_name}.sln"


class WindowsVisualStudioCreateCommand(WindowsVisualStudioMixin, WindowsCreateCommand):
    description = "Create and populate a Visual Studio project."


class WindowsVisualStudioUpdateCommand(WindowsVisualStudioCreateCommand, UpdateCommand):
    description = "Update an existing Visual Studio project."


class WindowsVisualStudioOpenCommand(WindowsVisualStudioMixin, OpenCommand):
    description = "Open an existing Visual Studio project."


class WindowsVisualStudioBuildCommand(WindowsVisualStudioMixin, BuildCommand):
    description = "Build a Visual Studio project."

    def verify_tools(self):
        super().verify_tools()
        VisualStudio.verify(self.tools)

    def build_app(self, app: BaseConfig, **kwargs):
        """Build the Visual Studio project.

        :param app: The config object for the app
        """
        self.logger.info("Building VisualStudio project...", prefix=app.app_name)

        with self.input.wait_bar("Building solution..."):
            try:
                self.tools.subprocess.run(
                    [
                        self.tools.visualstudio.msbuild_path,
                        f"{app.formal_name}.sln",
                        "-target:restore",
                        "-property:RestorePackagesConfig=true",
                        f"-target:{app.formal_name}",
                        "-property:Configuration=Release",
                    ],
                    check=True,
                    cwd=self.bundle_path(app),
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to build solution for {app.app_name}."
                ) from e


class WindowsVisualStudioRunCommand(WindowsVisualStudioMixin, WindowsRunCommand):
    description = "Run a Visual Studio project."


class WindowsVisualStudioPackageCommand(
    WindowsVisualStudioMixin,
    WindowsPackageCommand,
):
    description = "Package a Visual Studio project as an MSI."


class WindowsVisualStudioPublishCommand(WindowsVisualStudioMixin, PublishCommand):
    description = "Publish a Visual Studio project."


# Declare the briefcase command bindings
create = WindowsVisualStudioCreateCommand
update = WindowsVisualStudioUpdateCommand
open = WindowsVisualStudioOpenCommand
build = WindowsVisualStudioBuildCommand
run = WindowsVisualStudioRunCommand
package = WindowsVisualStudioPackageCommand
publish = WindowsVisualStudioPublishCommand
