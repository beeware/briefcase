import os
import shutil
import subprocess
from pathlib import Path

from requests import exceptions as requests_exceptions

from briefcase.exceptions import (
    BriefcaseCommandError,
    MissingToolError,
    NetworkFailure,
    NonManagedToolError,
)


class JDK:
    name = "java"
    full_name = "Java JDK"

    def __init__(self, command, java_home):
        self.command = command

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
        }.get(self.command.host_os)

        extension = {
            "Windows": "zip",
        }.get(self.command.host_os, "tar.gz")

        return (
            "https://github.com/AdoptOpenJDK/openjdk8-binaries/"
            f"releases/download/jdk{self.release}-{self.build}/"
            f"OpenJDK8U-jdk_x64_{platform}_hotspot_{self.release}{self.build}.{extension}"
        )

    @classmethod
    def verify(cls, command, install=True):
        """Verify that a Java 8 JDK exists.

        If ``JAVA_HOME`` is set, try that version. If it is a JRE, or its *not*
        a Java 8 JDK, download one.

        On macOS, also try invoking /usr/libexec/java_home. If that location
        points to a Java 8 JDK, use it.

        Otherwise, download a JDK from AdoptOpenJDK and unpack it into the
        ``~.briefcase`` path.

        :param command: The command that needs to perform the verification
            check.
        :param install: Should the tool be installed if it is not found?
        :returns: A valid Java JDK wrapper. If a JDK is not available, and was
            not installed, raises MissingToolError.
        """
        java_home = command.os.environ.get("JAVA_HOME", "")
        install_message = None

        # macOS has a helpful system utility to determine JAVA_HOME. Try it.
        if not java_home and command.host_os == "Darwin":
            try:
                # If no JRE/JDK is installed, /usr/libexec/java_home
                # raises an error.
                java_home = command.subprocess.check_output(
                    ["/usr/libexec/java_home"],
                    stderr=subprocess.STDOUT,
                ).strip("\n")
            except subprocess.CalledProcessError:
                # No java on this machine.
                pass

        if java_home:
            try:
                # If JAVA_HOME is defined, try to invoke javac.
                # This verifies that we have a JDK, not a just a JRE.
                output = command.subprocess.check_output(
                    [
                        os.fsdecode(Path(java_home) / "bin" / "javac"),
                        "-version",
                    ],
                    stderr=subprocess.STDOUT,
                )
                # This should be a string of the form "javac 1.8.0_144\n"
                version_str = output.strip("\n").split(" ")[1]
                vparts = version_str.split(".")
                if len(vparts) == 3 and vparts[:2] == ["1", "8"]:
                    # It appears to be a Java 8 JDK.
                    return JDK(command, java_home=Path(java_home))
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

            except FileNotFoundError:
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

        # If we've reached this point, any user-provided JAVA_HOME is broken;
        # use the Briefcase one.
        java_home = command.tools_path / "java"

        # The macOS download has a weird layout (inherited from the official Oracle
        # release). The actual JAVA_HOME is deeper inside the directory structure.
        if command.host_os == "Darwin":
            java_home = java_home / "Contents" / "Home"

        jdk = JDK(command, java_home=java_home)

        if jdk.exists():
            # Using briefcase-managed Java version
            return jdk
        if install:
            # We only display the warning messages on the pass where we actually
            # install the JDK.
            if install_message:
                command.logger.warning(install_message)
            command.logger.info(
                "The Java JDK was not found; downloading and installing...",
                prefix=cls.name,
            )
            jdk.install()
            return jdk
        else:
            raise MissingToolError("Java")

    def exists(self):
        return (self.java_home / "bin").exists()

    @property
    def managed_install(self):
        try:
            # Determine if java_home is relative to the .briefcase folder.
            # If java_home isn't inside .briefcase, this will raise a ValueError,
            # indicating it is a non-managed install.
            self.java_home.relative_to(self.command.tools_path)
            return True
        except ValueError:
            return False

    def install(self):
        """Download and install a JDK."""
        try:
            jdk_zip_path = self.command.download_url(
                url=self.adoptOpenJDK_download_url,
                download_path=self.command.tools_path,
            )
        except requests_exceptions.ConnectionError as e:
            raise NetworkFailure("download Java 8 JDK") from e

        with self.command.input.wait_bar("Installing AdoptOpenJDK..."):
            try:
                # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
                self.command.shutil.unpack_archive(
                    os.fsdecode(jdk_zip_path),
                    extract_dir=os.fsdecode(self.command.tools_path),
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

            # The tarball will unpack into ~.briefcase/tools/jdk8u242-b08
            # (or whatever name matches the current release).
            # We turn this into ~.briefcase/tools/java so we have a consistent name.
            java_unpack_path = (
                self.command.tools_path / f"jdk{self.release}-{self.build}"
            )
            java_unpack_path.rename(self.command.tools_path / "java")

    def uninstall(self):
        """Uninstall a JDK."""
        with self.command.input.wait_bar("Removing old JDK install..."):
            if self.command.host_os == "Darwin":
                self.command.shutil.rmtree(self.java_home.parent.parent)
            else:
                self.command.shutil.rmtree(self.java_home)

    def upgrade(self):
        """Upgrade an existing JDK install."""
        if not self.managed_install:
            raise NonManagedToolError("Java")
        if not self.exists():
            raise MissingToolError("Java")

        self.uninstall()
        self.install()
