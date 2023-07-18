from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError, MissingToolError
from briefcase.integrations.base import ManagedTool, ToolCache


class JDK(ManagedTool):
    name = "java"
    full_name = "Java JDK"

    # As of 12 May 2023, 17.0.7+7 is the current OpenJDK
    # https://adoptium.net/temurin/releases/
    JDK_MAJOR_VER = "17"
    JDK_RELEASE = "17.0.7"
    JDK_BUILD = "7"
    JDK_INSTALL_DIR_NAME = f"java{JDK_MAJOR_VER}"

    def __init__(self, tools: ToolCache, java_home: Path):
        super().__init__(tools=tools)
        self.java_home = java_home

    @property
    def OpenJDK_download_url(self):
        arch = {
            "x86_64": "x64",  # Linux\macOS x86-64
            "aarch64": "aarch64",  # Linux arm64
            "armv6l": "arm",  # Linux arm
            "arm64": "aarch64",  # macOS arm64
            "AMD64": "x64",  # Windows x86-64
        }.get(self.tools.host_arch)

        platform = {
            "Darwin": "mac",
            "Windows": "windows",
            "Linux": "linux",
        }.get(self.tools.host_os)

        extension = {
            "Windows": "zip",
        }.get(self.tools.host_os, "tar.gz")

        return (
            f"https://github.com/adoptium/temurin{self.JDK_MAJOR_VER}-binaries/"
            f"releases/download/jdk-{self.JDK_RELEASE}+{self.JDK_BUILD}/"
            f"OpenJDK{self.JDK_MAJOR_VER}U-jdk_{arch}_{platform}_hotspot_"
            f"{self.JDK_RELEASE}_{self.JDK_BUILD}.{extension}"
        )

    @classmethod
    def version_from_path(cls, tools: ToolCache, java_path: str | Path) -> str:
        """Return a JDK's version from a path by running ``<java_path>/bin/javac``.

        This will fail if the path contains a JRE instead of a JDK.

        Several exceptions can be raised for issues:
         - OSError - the ``javac`` executable doesn't exist
         - CalledProcessError - ``javac`` returned a non-zero value
         - IndexError - unparsable version value from ``javac``

        :param tools: ToolCache of available tools
        :param java_path: File path to a candidate JDK install
        :return: JDK release version; e.g. "17.0.7"
        """
        output = tools.subprocess.check_output(
            [
                os.fsdecode(Path(java_path) / "bin" / "javac"),
                "-version",
            ],
        )
        # javac's output should look like "javac 17.0.7\n"
        return output.strip("\n").split(" ")[1]

    @classmethod
    def verify_install(cls, tools: ToolCache, install: bool = True, **kwargs) -> JDK:
        """Verify that a Java JDK exists.

        If ``JAVA_HOME`` is set, try that version. If it is a JRE, or its *not*
        a Java JDK, download one.

        On macOS, also try invoking /usr/libexec/java_home. If that location
        points to a Java JDK, use it.

        Otherwise, download a JDK from OpenJDK and unpack it into the
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
        install_message = None

        if java_home := tools.os.environ.get("JAVA_HOME", ""):
            try:
                version_str = cls.version_from_path(tools, java_home)
                if version_str.split(".")[0] == cls.JDK_MAJOR_VER:
                    java = JDK(tools, java_home=Path(java_home))
                else:
                    install_message = f"""
*************************************************************************
** WARNING: JAVA_HOME does not point to a Java {cls.JDK_MAJOR_VER} JDK                  **
*************************************************************************

    Android requires a Java {cls.JDK_MAJOR_VER} JDK, but the location pointed to by the
    JAVA_HOME environment variable:

    {java_home}

    isn't a Java {cls.JDK_MAJOR_VER} JDK (it appears to be Java {version_str}).

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

        # macOS has a helpful system utility to determine JAVA_HOME. Try it.
        elif tools.host_os == "Darwin":
            try:
                # If /usr/libexec/java_home doesn't exist, OSError will be raised
                # If no JRE/JDK is installed, /usr/libexec/java_home raises an error
                java_home = tools.subprocess.check_output(
                    ["/usr/libexec/java_home"],
                ).strip("\n")
            except (OSError, subprocess.CalledProcessError):
                pass  # No java on this machine
            else:
                try:
                    version_str = cls.version_from_path(tools, java_home)
                    if version_str.split(".")[0] == cls.JDK_MAJOR_VER:
                        java = JDK(tools, java_home=Path(java_home))
                except (OSError, subprocess.CalledProcessError, IndexError):
                    pass  # do not alert user if macOS found an unqualified JDK

        if java is None:
            # Inform the user if the user-specified JDK wasn't valid
            if install_message:
                tools.logger.warning(install_message)

            # Use the Briefcase JDK install
            java_home = tools.base_path / cls.JDK_INSTALL_DIR_NAME

            # The macOS download has a weird layout (inherited from the official Oracle
            # release). The actual JAVA_HOME is deeper inside the directory structure.
            if tools.host_os == "Darwin":
                java_home = java_home / "Contents" / "Home"

            java = JDK(tools=tools, java_home=java_home)

            if not java.exists():
                if install:
                    tools.logger.info(
                        f"A Java {cls.JDK_MAJOR_VER} JDK was not found; downloading and installing...",
                        prefix=cls.name,
                    )
                    java.install()
                else:
                    raise MissingToolError("Java")

        tools.java = java
        return java

    def exists(self) -> bool:
        return (self.java_home / "bin").exists()

    @property
    def managed_install(self) -> bool:
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
            url=self.OpenJDK_download_url,
            download_path=self.tools.base_path,
            role=f"Java {self.JDK_MAJOR_VER} JDK",
        )

        with self.tools.input.wait_bar("Installing OpenJDK..."):
            try:
                # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
                self.tools.shutil.unpack_archive(
                    os.fsdecode(jdk_zip_path),
                    extract_dir=os.fsdecode(self.tools.base_path),
                )
            except (shutil.ReadError, EOFError) as e:
                raise BriefcaseCommandError(
                    f"""\
Unable to unpack OpenJDK ZIP file. The download may have been interrupted
or corrupted.

Delete {jdk_zip_path} and run briefcase again.
"""
                ) from e

            jdk_zip_path.unlink()  # Zip file no longer needed once unpacked.

            # The tarball will unpack into <briefcase data dir>/tools/jdk-17.0.7+7
            # (or whatever name matches the current release).
            # We turn this into <briefcase data dir>/tools/java so we have a consistent name.
            java_unpack_path = (
                self.tools.base_path / f"jdk-{self.JDK_RELEASE}+{self.JDK_BUILD}"
            )
            java_unpack_path.rename(self.tools.base_path / self.JDK_INSTALL_DIR_NAME)

    def uninstall(self):
        """Uninstall a JDK."""
        with self.tools.input.wait_bar("Removing old JDK install..."):
            if self.tools.host_os == "Darwin":
                self.tools.shutil.rmtree(self.java_home.parent.parent)
            else:
                self.tools.shutil.rmtree(self.java_home)
