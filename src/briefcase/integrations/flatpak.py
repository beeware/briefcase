import subprocess

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.base import Tool, ToolCache


class Flatpak(Tool):
    name = "flatpak"
    full_name = "Flatpak"

    DEFAULT_REPO_ALIAS = "flathub"
    DEFAULT_REPO_URL = "https://flathub.org/repo/flathub.flatpakrepo"

    DEFAULT_RUNTIME = "org.freedesktop.Platform"
    DEFAULT_RUNTIME_VERSION = "21.08"
    DEFAULT_SDK = "org.freedesktop.Sdk"

    def __init__(self, tools: ToolCache):
        self.tools = tools

    @classmethod
    def verify(cls, tools: ToolCache):
        """Verify that the Flatpak toolchain is available.

        :param tools: ToolCache of available tools
        :returns: A wrapper for the Flatpak tools.
        """
        # short circuit since already verified and available
        if hasattr(tools, "flatpak"):
            return tools.flatpak

        flatpak = Flatpak(tools=tools)
        try:
            output = tools.subprocess.check_output(["flatpak", "--version"]).strip("\n")
            parts = output.split(" ")
            try:
                if parts[0] == "Flatpak":
                    version = parts[1].split(".")
                    if int(version[0]) < 1:
                        raise BriefcaseCommandError(
                            "Briefcase requires Flatpak 1.0 or later."
                        )
                else:
                    raise ValueError(f"Unexpected tool name {parts[0]}")
            except (ValueError, IndexError):
                tools.logger.warning(
                    """\
*************************************************************************
** WARNING: Unable to determine the version of Flatpak                 **
*************************************************************************

    Briefcase will proceed, assuming everything is OK. If you
    experience problems, this is almost certainly the cause of those
    problems.

    Please report this as a bug at:

      https://github.com/beeware/briefcase/issues/new

    In your report, please including the output from running:

      flatpak --version

    from the command prompt.

*************************************************************************
"""
                )

        except OSError as e:
            raise BriefcaseCommandError(
                """\
Briefcase requires the Flatpak toolchain, but it does not appear to be installed.

Instructions for installing the Flatpak toolchain can be found at:

    https://flatpak.org/setup/

You must install both flatpak and flatpak-builder.
"""
            ) from e
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError("Unable to invoke flatpak.") from e

        try:
            output = tools.subprocess.check_output(
                ["flatpak-builder", "--version"]
            ).strip("\n")

            parts = output.split(" ")
            try:
                if parts[0] == "flatpak-builder":
                    version = parts[1].split(".")
                    if int(version[0]) < 1:
                        raise BriefcaseCommandError(
                            "Briefcase requires flatpak-builder 1.0 or later."
                        )
                else:
                    raise ValueError(f"Unexpected tool name {parts[0]}")
            except (ValueError, IndexError):
                tools.logger.warning(
                    """\
*************************************************************************
** WARNING: Unable to determine the version of flatpak-builder         **
*************************************************************************

    Briefcase will proceed, assuming everything is OK. If you
    experience problems, this is almost certainly the cause of those
    problems.

    Please report this as a bug at:

      https://github.com/beeware/briefcase/issues/new

    In your report, please including the output from running:

      flatpak-builder --version

    from the command prompt.

*************************************************************************
"""
                )

        except OSError as e:
            raise BriefcaseCommandError(
                """\
Briefcase requires the full Flatpak development toolchain, but flatpak-builder
does not appear to be installed.

Instructions for installing the Flatpak toolchain can be found at:

    https://flatpak.org/setup/

You must install both flatpak and flatpak-builder.
"""
            ) from e
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError("Unable to invoke flatpak-builder.") from e

        tools.flatpak = flatpak
        return flatpak

    def verify_repo(self, repo_alias, url):
        """Verify that the Flatpak repository has been registered.

        :param repo_alias: The alias to use when registering the repo.
        :param url: The URL of the Flatpak repo.
        """
        try:
            self.tools.subprocess.run(
                [
                    "flatpak",
                    "remote-add",
                    "--user",
                    "--if-not-exists",
                    repo_alias,
                    url,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to add Flatpak repo {url} with alias {repo_alias}."
            ) from e

    def verify_runtime(self, repo_alias, runtime, runtime_version, sdk):
        """Verify that a specific Flatpak runtime and SDK are available.

        :param repo_alias: The alias of the repo where the runtime and SDK are
            stored.
        :param runtime: The identifier of the Flatpak runtime
        :param runtime_version: The version of the Flatpak runtime
        :param sdk: The Flatpak SDK
        """
        try:
            self.tools.subprocess.run(
                [
                    "flatpak",
                    "install",
                    "--assumeyes",
                    "--user",
                    repo_alias,
                    f"{runtime}/{self.tools.host_arch}/{runtime_version}",
                    f"{sdk}/{self.tools.host_arch}/{runtime_version}",
                ],
                check=True,
                # flatpak install uses many animations that cannot be disabled
                stream_output=False,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to install Flatpak runtime {runtime}/{self.tools.host_arch}/{runtime_version} "
                f"and SDK {sdk}/{self.tools.host_arch}/{runtime_version} from repo {repo_alias}."
            ) from e

    def build(self, bundle, app_name, path):
        """Build a Flatpak manifest.

        On success, the app is installed into the user's local Flatpak install,
        and a shell script is created that can be used to start the app. The
        shell file isn't really needed to start the app, but it serves as a
        marker for a successful build that Briefcase can use.

        :param bundle: The bundle identifier for the app being built.
        :param app_name: The app name.
        :param path: The path to the folder containing the app's Flatpak
            manifest file.
        """
        try:
            self.tools.subprocess.run(
                [
                    "flatpak-builder",
                    "--force-clean",
                    # Archive into a local repository
                    "--repo",
                    "repo",
                    # Install the app into the user space
                    "--install",
                    "--user",
                    "build",
                    "manifest.yml",
                ],
                check=True,
                cwd=path,
            )

            # Create a marker file to indicate a build has completed.
            # For bonus points, the marker file also is executable
            # and is an alias for the command that would actually start
            # the flatpak.
            bin_path = path / f"{bundle}.{app_name}"
            with bin_path.open("w", encoding="utf-8") as f:
                f.write(
                    f"""\
#!/bin/sh
# echo To run this flatpak, run:
flatpak run {bundle}.{app_name}
"""
                )
                self.tools.os.chmod(bin_path, 0o755)
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Error while building app {app_name}.") from e

    def run(self, bundle, app_name, args=None, main_module=None):
        """Run a Flatpak in a way that allows for log streaming.

        :param bundle: The bundle identifier for the app being built.
        :param app_name: The app name.
        :param args: (Optional) The list of arguments to pass to the app
        :param main_module: (Optional) The main module to run. Only required if you
            want to override the default main module for the app.
        :returns: A Popen object for the running app.
        """
        if main_module:
            # Set a BRIEFCASE_MAIN_MODULE environment variable
            # to override the module at startup
            kwargs = {
                "env": {
                    "BRIEFCASE_MAIN_MODULE": main_module,
                }
            }
        else:
            kwargs = {}

        return self.tools.subprocess.Popen(
            [
                "flatpak",
                "run",
                f"{bundle}.{app_name}",
            ]
            + ([] if args is None else args),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            **kwargs,
        )

    def bundle(self, repo_url, bundle, app_name, version, build_path, output_path):
        """Bundle a Flatpak for distribution.

        Generates a standalone .flatpak file that can be installed into another user's
        Flatpak repository.

        :param repo_url: The URL of the repository that contains the runtime
            used by the app.
        :param bundle: The bundle identifier for the app being built.
        :param app_name: The app name.
        :param version: The version of the app being built.
        :param build_path: The path where the flatpak was built. This path will
            contain the repo where the built flatpak was exported.
        :param output_path: The path of the output file to create as an export.
        """
        try:
            self.tools.subprocess.run(
                [
                    "flatpak",
                    "build-bundle",
                    # Set the repo where the runtime can be found
                    "--runtime-repo",
                    repo_url,
                    # Sign the export
                    # "--gpg-sign", "..."
                    "repo",
                    output_path,
                    f"{bundle}.{app_name}",
                    version,
                ],
                check=True,
                cwd=build_path,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to build a Flatpak bundle for app {app_name}."
            ) from e
