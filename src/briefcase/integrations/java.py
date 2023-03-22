import os
import shutil
import subprocess
from pathlib import Path

from briefcase.exceptions import (
    BriefcaseCommandError,
    MissingToolError,
    NonManagedToolError,
)
from briefcase.integrations.base import Tool, ToolCache


class JDK(Tool):
    name = "java"
    full_name = "Java JDK"

    def __init__(self, tools: ToolCache, java_home: Path):
        self.tools = tools

        # As of April 10 2020, 8u242-b08 is the current AdoptOpenJDK
        # https://adoptopenjdk.net/releases.html
        self.release = "8u242"
        self.build = "b08"

        self.java_home = java_home

    @property
    def adoptOpenJDK_download_url(self):
        platform = {
            "Darwin": "mac",
            "Windows": "windows",
            "Linux": "linux",
        }.get(self.tools.host_os)

        extension = {
            "Windows": "zip",
        }.get(self.tools.host_os, "tar.gz")

        return (
            "https://github.com/AdoptOpenJDK/openjdk8-binaries/"
            f"releases/download/jdk{self.release}-{self.build}/"
            f"OpenJDK8U-jdk_x64_{platform}_hotspot_{self.release}{self.build}.{extension}"
        )

    @classmethod
    def verify(cls, tools: ToolCache, install=True):
        """Verify that a Java 8 JDK exists.

        If ``JAVA_HOME`` is set, try that version. If it is a JRE, or its *not*
        a Java 8 JDK, download one.

        On macOS, also try invoking /usr/libexec/java_home. If that location
        points to a Java 8 JDK, use it.

        Otherwise, download a JDK from AdoptOpenJDK and unpack it into the
        briefcase data directory.

        :param tools: ToolCache of available tools
        :param install: Should the tool be installed if it is not found?
        :returns: A valid Java JDK wrapper. If a JDK is not available, and was
            not installed, raises MissingToolError.
        """
        # short circuit since already verified and available
        if hasattr(tools, "java"):
            return tools.java

        java = None
        java_home = tools.os.environ.get("JAVA_HOME", "")
        install_message = None

        if tools.host_arch == "arm64" and tools.host_os == "Darwin":
            # Java 8 is not available for macOS on ARM64, so we will require Rosetta.
            cls.verify_rosetta(tools)

        # macOS has a helpful system utility to determine JAVA_HOME. Try it.
        if not java_home and tools.host_os == "Darwin":
            try:
                # If no JRE/JDK is installed, /usr/libexec/java_home
                # raises an error.
                java_home = tools.subprocess.check_output(
                    ["/usr/libexec/java_home"],
                ).strip("\n")
            except subprocess.CalledProcessError:
                # No java on this machine.
                pass

        if java_home:
            try:
                # If JAVA_HOME is defined, try to invoke javac.
                # This verifies that we have a JDK, not a just a JRE.
                output = tools.subprocess.check_output(
                    [
                        os.fsdecode(Path(java_home) / "bin" / "javac"),
                        "-version",
                    ],
                )
                # This should be a string of the form "javac 1.8.0_144\n"
                version_str = output.strip("\n").split(" ")[1]
                vparts = version_str.split(".")
                if len(vparts) == 3 and vparts[:2] == ["1", "8"]:
                    # It appears to be a Java 8 JDK.
                    java = JDK(tools, java_home=Path(java_home))
                else:
                    # It's not a Java 8 JDK.
                    install_message = f"""
*************************************************************************
** WARNING: JAVA_HOME does not point to a Java 8 JDK                   **
*************************************************************************

    Android requires a Java 8 JDK, but the location pointed to by the
    JAVA_HOME environment variable:

    {java_home}

    isn't a Java 8 JDK (it appears to be Java {version_str}).

    Briefcase will use its own JDK instance.

*************************************************************************

"""

            except OSError:
                install_message = f"""
*************************************************************************
** WARNING: JAVA_HOME does not point to a JDK                          **
*************************************************************************

    The location pointed to by the JAVA_HOME environment variable:

    {java_home}

    does not appear to be a JDK. It may be a Java Runtime Environment.

    Briefcase will use its own JDK instance.

*************************************************************************

"""

            except subprocess.CalledProcessError:
                install_message = f"""
*************************************************************************
** WARNING: Unable to invoke the Java compiler                         **
*************************************************************************

    Briefcase received an unexpected error when trying to invoke javac,
    the Java compiler, at the location indicated by the JAVA_HOME
    environment variable.

    Briefcase will continue by downloading and using its own JDK.

    Please report this as a bug at:

        https://github.com/beeware/briefcase/issues/new


    In your report, please including the output from running:

        {java_home}/bin/javac -version

    from the command prompt.

*************************************************************************

"""

            except IndexError:
                install_message = f"""
*************************************************************************
** WARNING: Unable to determine the version of Java that is installed  **
*************************************************************************

    Briefcase was unable to interpret the version information returned
    by the Java compiler at the location indicated by the JAVA_HOME
    environment variable.

    Briefcase will continue by downloading and using its own JDK.

    Please report this as a bug at:

        https://github.com/beeware/briefcase/issues/new


    In your report, please including the output from running:

        {java_home}/bin/javac -version

    from the command prompt.

*************************************************************************

"""

        if java is None:
            # If we've reached this point, any user-provided JAVA_HOME is broken;
            # use the Briefcase one.
            java_home = tools.base_path / "java"

            # The macOS download has a weird layout (inherited from the official Oracle
            # release). The actual JAVA_HOME is deeper inside the directory structure.
            if tools.host_os == "Darwin":
                java_home = java_home / "Contents" / "Home"

            java = JDK(tools, java_home=java_home)

            if not java.exists():
                if install:
                    # We only display the warning messages on the pass where we actually
                    # install the JDK.
                    if install_message:
                        tools.logger.warning(install_message)
                    tools.logger.info(
                        "The Java JDK was not found; downloading and installing...",
                        prefix=cls.name,
                    )
                    java.install()
                else:
                    raise MissingToolError("Java")

        tools.java = java
        return java

    def exists(self):
        return (self.java_home / "bin").exists()

    @property
    def managed_install(self):
        try:
            # Determine if java_home is relative to the briefcase data directory.
            # If java_home isn't inside this directory, this will raise a ValueError,
            # indicating it is a non-managed install.
            self.java_home.relative_to(self.tools.base_path)
            return True
        except ValueError:
            return False

    def install(self):
        """Download and install a JDK."""
        jdk_zip_path = self.tools.download.file(
            url=self.adoptOpenJDK_download_url,
            download_path=self.tools.base_path,
            role="Java 8 JDK",
        )

        with self.tools.input.wait_bar("Installing AdoptOpenJDK..."):
            try:
                # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
                self.tools.shutil.unpack_archive(
                    os.fsdecode(jdk_zip_path),
                    extract_dir=os.fsdecode(self.tools.base_path),
                )
            except (shutil.ReadError, EOFError) as e:
                raise BriefcaseCommandError(
                    f"""\
Unable to unpack AdoptOpenJDK ZIP file. The download may have been interrupted
or corrupted.

Delete {jdk_zip_path} and run briefcase again.
"""
                ) from e

            jdk_zip_path.unlink()  # Zip file no longer needed once unpacked.

            # The tarball will unpack into <briefcase data dir>/tools/jdk8u242-b08
            # (or whatever name matches the current release).
            # We turn this into <briefcase data dir>/tools/java so we have a consistent name.
            java_unpack_path = self.tools.base_path / f"jdk{self.release}-{self.build}"
            java_unpack_path.rename(self.tools.base_path / "java")

    def uninstall(self):
        """Uninstall a JDK."""
        with self.tools.input.wait_bar("Removing old JDK install..."):
            if self.tools.host_os == "Darwin":
                self.tools.shutil.rmtree(self.java_home.parent.parent)
            else:
                self.tools.shutil.rmtree(self.java_home)

    def upgrade(self):
        """Upgrade an existing JDK install."""
        if not self.managed_install:
            raise NonManagedToolError("Java")
        if not self.exists():
            raise MissingToolError("Java")

        self.uninstall()
        self.install()

    @classmethod
    def verify_rosetta(cls, tools):
        try:
            tools.subprocess.check_output(["arch", "-x86_64", "true"])
        except subprocess.CalledProcessError:
            tools.logger.info(
                """\
This command requires Rosetta, but it does not appear to be installed.
Briefcase will attempt to install it now.
"""
            )
            try:
                tools.subprocess.run(
                    ["softwareupdate", "--install-rosetta", "--agree-to-license"],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError("Failed to install Rosetta") from e
