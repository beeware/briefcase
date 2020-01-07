import os
import re
import struct
import subprocess
import sys
import uuid
from pathlib import Path

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.windows import WindowsMixin


class WindowsMSIMixin(WindowsMixin):
    output_format = 'msi'

    def binary_path(self, app):
        return self.platform_path / app.formal_name

    def distribution_path(self, app):
        return self.platform_path / '{app.formal_name}-{app.version}.msi'.format(app=app)

    def verify_tools(self):
        super().verify_tools()
        if self.host_os != 'Windows':
            raise BriefcaseCommandError("""
A Windows MSI installer can only be created on Windows.
""")

        # Look for the WiX environment variable
        wix_path = Path(os.getenv('WIX', ''))

        # Set up the paths for the WiX executables we will use.
        self.heat_exe = wix_path / 'bin' / 'heat.exe'
        self.light_exe = wix_path / 'bin' / 'light.exe'
        self.candle_exe = wix_path / 'bin' / 'candle.exe'
        if not wix_path:
            raise BriefcaseCommandError("""
WiX Toolset is not installed.

Please install the latest stable release from:

    https://wixtoolset.org/

If WiX is already installed, ensure the WIX environment variable has been set,
and that it point to the installed location.

If you're using Windows 10, you may need to enable the .NET 3.5 framework
before installing WiX. Open the Control Panel, select "Programs and Features",
then "Turn Windows features on or off". Ensure ".NET Framework 3.5 (Includes
.NET 2.0 and 3.0)" is enabled.
""")
        elif not (
            self.heat_exe.exists()
            and self.light_exe.exists()
            and self.candle_exe.exists()
        ):
            raise BriefcaseCommandError("""
The WIX environment variable does not point to an install of the WiX Toolset.
Current value: {wix_path!r}
""".format(wix_path=wix_path))


class WindowsMSICreateCommand(WindowsMSIMixin, CreateCommand):
    description = "Create and populate a Windows app."

    @property
    def support_package_url_query(self):
        """
        The query arguments to use in a support package query request.
        """
        return [
            ('platform', self.platform),
            ('version', self.python_version_tag),
            ('arch', "amd64" if (struct.calcsize("P") * 8) == 64 else "win32"),
        ]

    def output_format_template_context(self, app: BaseConfig):
        """
        Additional template context required by the output format.

        :param app: The config object for the app
        """
        # WiX requires a 3-element, integer-only version number. If a version
        # triple isn't explicitly provided, generate one by stripping any
        # non-numeric portions from the version number.
        # If there are less than 3 numeric parts, 0s will be appended.
        try:
            version_triple = app.version_triple
        except AttributeError:
            version_triple = '.'.join(
                (re.findall(r'\d+', app.version) + ['0', '0'])[:3]
            )

        # The application needs a unique GUID.
        # This is used to track the application, even if the application
        # name changes. We can generate a default GUID using the bundle
        # and the formal name; but you'll need to manually set this value
        # if you ever change those two keys.
        try:
            guid = app.guid
        except AttributeError:
            # Create a DNS domain by reversing the bundle identifier
            domain = '.'.join([app.app_name] + app.bundle.split('.')[::-1])
            guid = uuid.uuid5(uuid.NAMESPACE_DNS, domain)
            print("Assigning {app.app_name} an application GUID of {guid}".format(
                app=app,
                guid=guid,
            ))

        return {
            'version_triple': version_triple,
            'guid': str(guid),
        }

    def install_app_support_package(self, app: BaseConfig):
        """
        Install, then modify the default support package.
        """
        # Install the support package using the normal install logic.
        super().install_app_support_package(app)

        # We need to add a ._pth file to include app and app_packages as
        # part of the standard PYTHONPATH. Write a _pth file directly into
        # the support folder, overwriting the default one.
        version_tag = "{sys.version_info.major}{sys.version_info.minor}".format(
            sys=sys
        )
        pth_file = self.support_path(app) / 'python{version_tag}._pth'.format(
            version_tag=version_tag
        )
        with pth_file.open('w') as f:
            f.write('python{version_tag}.zip\n'.format(version_tag=version_tag))
            f.write(".\n")
            f.write("..\\\\app\n")
            f.write("..\\\\app_packages\n")


class WindowsMSIUpdateCommand(WindowsMSIMixin, UpdateCommand):
    description = "Update an existing Windows app."


class WindowsMSIBuildCommand(WindowsMSIMixin, BuildCommand):
    description = "Build a Windows app."


class WindowsMSIRunCommand(WindowsMSIMixin, RunCommand):
    description = "Run a Windows app."

    def run_app(self, app: BaseConfig, **kwargs):
        """
        Start the application.

        :param app: The config object for the app
        :param base_path: The path to the project directory.
        """
        print()
        print('[{app.app_name}] Starting app...'.format(
            app=app
        ))
        try:
            print()
            self.subprocess.run(
                [
                    str(self.binary_path(app) / 'src' / 'python' / 'pythonw.exe'),
                    "-m", app.module_name
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Unable to start app {app.app_name}.".format(app=app)
            )


class WindowsMSIPackageCommand(WindowsMSIMixin, PackageCommand):
    description = "Package an MSI for a Windows app."

    def package_app(self, app: BaseConfig, **kwargs):
        """
        Build an application.

        :param app: The application to build
        """
        print()
        print("[{app.app_name}] Building MSI...".format(app=app))

        try:
            print()
            print("Compiling application manifest...")
            self.subprocess.run(
                [
                    str(self.heat_exe),
                    "dir",
                    "src",
                    "-nologo",  # Don't display startup text
                    "-gg",  # Generate GUIDs
                    "-sfrag",  # Suppress fragment generation for directories
                    "-sreg",  # Suppress registry harvesting
                    "-srd",  # Suppress harvesting the root directory
                    "-scom",  # Suppress harvesting COM components
                    "-dr", "{app.module_name}_ROOTDIR".format(app=app),  # Root directory reference name
                    "-cg", "{app.module_name}_COMPONENTS".format(app=app),  # Root component group name
                    "-var", "var.SourceDir",  # variable to use as the source dir
                    "-out", "{app.app_name}-manifest.wxs".format(app=app),
                ],
                check=True,
                cwd=str(self.bundle_path(app))
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "Unable to generate manifest for app {app.app_name}.".format(app=app)
            )

        try:
            print()
            print("Compiling application installer...")
            self.subprocess.run(
                [
                    str(self.candle_exe),
                    "-nologo",  # Don't display startup text
                    "-ext", "WixUtilExtension",
                    "-ext", "WixUIExtension",
                    "-dSourceDir=src",
                    "{app.app_name}.wxs".format(app=app),
                    "{app.app_name}-manifest.wxs".format(app=app),
                ],
                check=True,
                cwd=str(self.bundle_path(app))
            )
        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "Unable to compile app {app.app_name}.".format(app=app)
            )

        try:
            print()
            print("Linking application installer...")
            self.subprocess.run(
                [
                    str(self.light_exe),
                    "-nologo",  # Don't display startup text
                    "-ext", "WixUtilExtension",
                    "-ext", "WixUIExtension",
                    "-o", str(self.distribution_path(app)),
                    "{app.app_name}.wixobj".format(app=app),
                    "{app.app_name}-manifest.wixobj".format(app=app),
                ],
                check=True,
                cwd=str(self.bundle_path(app))
            )
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Unable to link app {app.app_name}.".format(app=app)
            )


class WindowsMSIPublishCommand(WindowsMSIMixin, PublishCommand):
    description = "Publish a Windows MSI."


# Declare the briefcase command bindings
create = WindowsMSICreateCommand  # noqa
update = WindowsMSIUpdateCommand  # noqa
build = WindowsMSIBuildCommand  # noqa
run = WindowsMSIRunCommand  # noqa
package = WindowsMSIPackageCommand  # noqa
publish = WindowsMSIPublishCommand  # noqa
