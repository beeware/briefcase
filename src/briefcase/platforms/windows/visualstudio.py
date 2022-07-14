import subprocess
from pathlib import Path

from briefcase.commands import BuildCommand, PublishCommand, UpdateCommand
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


class WindowsVisualStudioCreateCommand(WindowsVisualStudioMixin, WindowsCreateCommand):
    description = "Create and populate a Visual Studio app project."


class WindowsVisualStudioUpdateCommand(WindowsVisualStudioMixin, UpdateCommand):
    description = "Update an existing Visual Studio app project."


class WindowsVisualStudioBuildCommand(WindowsVisualStudioMixin, BuildCommand):
    description = "Build a Visual Studio app project."

    def verify_tools(self):
        super().verify_tools()
        self.visualstudio = VisualStudio.verify(self)

    def build_app(self, app: BaseConfig, **kwargs):
        """Build the Visual Studio project.

        :param app: The config object for the app
        """
        self.logger.info("Building VisualStudio project...", prefix=app.app_name)

        with self.input.wait_bar("Building solution..."):
            try:
                self.subprocess.run(
                    [
                        self.visualstudio.msbuild_path,
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
    description = "Run a Visual Studio app project."


class WindowsVisualStudioPackageCommand(
    WindowsVisualStudioMixin,
    WindowsPackageCommand,
):
    description = "Package a Visual Studio app project as an MSI."


class WindowsVisualStudioPublishCommand(WindowsVisualStudioMixin, PublishCommand):
    description = "Publish a Visual Studio app project."


# Declare the briefcase command bindings
create = WindowsVisualStudioCreateCommand  # noqa
update = WindowsVisualStudioUpdateCommand  # noqa
build = WindowsVisualStudioBuildCommand  # noqa
run = WindowsVisualStudioRunCommand  # noqa
package = WindowsVisualStudioPackageCommand  # noqa
publish = WindowsVisualStudioPublishCommand  # noqa
