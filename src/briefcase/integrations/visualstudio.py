import subprocess
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError, CommandOutputParseError
from briefcase.integrations.base import Tool, ToolCache
from briefcase.integrations.subprocess import json_parser


class VisualStudio(Tool):
    name = "visualstudio"
    full_name = "Visual Studio"
    VSCODE_REQUIRED_COMPONENTS = """
    * .NET Desktop Development
      - Default packages
    * Desktop Development with C++
      - Default packages; plus
      - C++/CLI support for v143 build tools
"""

    def __init__(
        self,
        tools: ToolCache,
        msbuild_path: Path,
        install_metadata: dict = None,
    ):
        self.tools = tools
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
    def verify(cls, tools: ToolCache):
        """Verify that Visual Studio is available.

        :param tools: ToolCache of available tools
        :returns: A Visual Studio tool wrapper. Raises an exception if
            Visual Studio is not available.
        """
        # short circuit since already verified and available
        if hasattr(tools, "visualstudio"):
            return tools.visualstudio

        visualstudio = None

        # Try running MSBuild, assuming it is on the PATH.
        try:
            tools.subprocess.check_output(["MSBuild.exe", "--version"])

            # Create an explicit VisualStudio, with no install metadata
            visualstudio = VisualStudio(tools, msbuild_path=Path("MSBuild.exe"))
        except FileNotFoundError:
            # MSBuild isn't on the path
            pass
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                "MSBuild is on the path, but Briefcase cannot start it."
            ) from e

        # try to find Visual Studio
        if visualstudio is None:
            # Look for an %MSBUILD% environment variable
            try:
                msbuild_path = Path(tools.os.environ["MSBUILD"])
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
                    Path(tools.os.environ["ProgramFiles(x86)"])
                    / "Microsoft Visual Studio"
                    / "Installer"
                    / "vswhere.exe"
                )
                if not vswhere_path.exists():
                    raise BriefcaseCommandError(
                        f"""\
Visual Studio does not appear to be installed. Visual Studio 2022 Community
Edition can be obtained as a free download from:

    https://visualstudio.microsoft.com/vs/community/

When you install Visual Studio, ensure you install the following workloads
and additional components:
{cls.VSCODE_REQUIRED_COMPONENTS}
If you have Visual Studio installed in a non-default location, you must
either put MSBuild.exe in your path, or define an MSBUILD environment
variable that points at the MSBuild.exe provided by your Visual Studio
installation.

"""
                    )

                # Retrieve metadata for Visual Studio install
                try:
                    install_metadata = tools.subprocess.parse_output(
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
                    OSError,
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
                        f"""\
Your Visual Studio installation does not appear to provide MSBuild.
Ensure that Visual Studio following workloads and components installed:
{cls.VSCODE_REQUIRED_COMPONENTS}
Then restart Briefcase.
"""
                    )

            # Try to invoke MSBuild at the established location
            try:
                tools.subprocess.check_output([msbuild_path, "--version"])
            except (subprocess.CalledProcessError, OSError):
                raise BriefcaseCommandError(
                    "MSBuild appears to exist, but Briefcase can't start it."
                )

            visualstudio = VisualStudio(
                tools,
                msbuild_path=msbuild_path,
                install_metadata=install_metadata,
            )

        tools.visualstudio = visualstudio
        return visualstudio

    @property
    def managed_install(self):
        return False
