import subprocess
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError, CommandOutputParseError
from briefcase.integrations.subprocess import json_parser


class VisualStudio:
    name = "visualstudio"
    VSCODE_REQUIRED_COMPONENTS = """
    * .NET Desktop Development
      - Default packages
    * Desktop Development with C++
      - Default packages; plus
      - C++/CLI support for v143 build tools
"""

    def __init__(self, command, msbuild_path, install_metadata=None):
        self.command = command
        self._msbuild_path = msbuild_path
        self._install_metadata = install_metadata

    @property
    def msbuild_path(self):
        """The path to the MSBuild executable."""
        return self._msbuild_path

    @property
    def install_metadata(self):
        """Metadata about the Visual Studio install.

        Will be ``None`` if MSBuild the path to MSBuild has been provided
        explicitly, or is on the path.

        Otherwise, a dictionary containing the install details from VSWhere.
        """
        return self._install_metadata

    @classmethod
    def verify(cls, command):
        """Verify that Visual Studio is available.

        :param command: The command that needs to use Visual Studio
        :param install: Should the tool be installed if it is not found?
        :returns: A Visual Studio tool wrapper. Raises an exception if
            Visual Studio is not available.
        """
        # Try running MSBuild, assuming it is on the PATH.
        try:
            command.subprocess.check_output(
                ["MSBuild.exe", "--version"],
                stderr=subprocess.STDOUT,
            )

            # Create an explicit VisualStudio, with no install metadata
            return VisualStudio(command, msbuild_path=Path("MSBuild.exe"))
        except FileNotFoundError:
            # MSBuild isn't on the path
            pass
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                """MSBuild is on the path, but Briefcase cannot start it."""
            ) from e

        # Look for an %MSBUILD% environment variable
        try:
            msbuild_path = Path(command.os.environ["MSBUILD"])
            install_metadata = None

            if not msbuild_path.exists():
                # The location referenced by %MSBUILD% doesn't exist
                raise BriefcaseCommandError(
                    f"""\
The location referenced by the environment variable MSBUILD:

    {msbuild_path}

does not appear to point to a MSBuild executable. Correct
or unset the environment variable; then re-run Briefcase.

"""
                )

        except KeyError:
            # No %MSBUILD% environment variable. Look for vswhere.exe
            vswhere_path = (
                Path(command.os.environ["ProgramFiles(x86)"])
                / "Microsoft Visual Studio"
                / "Installer"
                / "vswhere.exe"
            )
            if not vswhere_path.exists():
                raise BriefcaseCommandError(
                    """\
Visual Studio does not appear to be installed. Visual Studio 2022 Community
Edition can be obtained as a free download from:

    https://visualstudio.microsoft.com/vs/community/

When you install Visual Studio, ensure you install the following workloads
and additional components:
{VSCODE_REQUIRED_COMPONENTS}
If you have Visual Studio installed in a non-default location, you must
either put MSBuild.exe in your path, or define an MSBUILD environment
variable that points at the MSBuild.exe provided by your Visual Studio
installation.

"""
                )
            try:
                install_metadata = command.subprocess.parse_output(
                    json_parser,
                    [
                        vswhere_path,
                        "-latest",
                        "-prerelease",
                        "-format",
                        "json",
                    ],
                    stderr=subprocess.STDOUT,
                )[0]
            except (
                IndexError,
                KeyError,
                CommandOutputParseError,
                subprocess.CalledProcessError,
            ) as e:
                raise BriefcaseCommandError(
                    f"""\
Visual Studio appears to exist, but Briefcase can't retrieve installation metadata.
Please report this as a bug at:

    https://github.com/beeware/briefcase/issues/new

In your report, please including the output from running:

    {vswhere_path}

from the command prompt.

"""
                ) from e

            msbuild_path = (
                Path(install_metadata["installationPath"])
                / "MSBuild"
                / "Current"
                / "Bin"
                / "MSBuild.exe"
            )
            if not msbuild_path.exists():
                raise BriefcaseCommandError(
                    """\
Your Visual Studio installation does not appear to provide MSBuild.
Ensure that Visual Studio following workloads and components installed:
{VSCODE_REQUIRED_COMPONENTS}
Then restart Briefcase.
"""
                )

        try:
            # Try to invoke MSBuild at the established location
            command.subprocess.check_output(
                [msbuild_path, "--version"], stderr=subprocess.STDOUT
            )

        except subprocess.CalledProcessError:
            raise BriefcaseCommandError(
                "MSBuild appears to exist, but Briefcase can't start it."
            )

        return VisualStudio(
            command,
            msbuild_path=msbuild_path,
            install_metadata=install_metadata,
        )

    @property
    def managed_install(self):
        return False
