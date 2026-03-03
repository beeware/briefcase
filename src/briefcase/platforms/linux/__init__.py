import ast
import re
import subprocess
import sys
from pathlib import Path

from briefcase.commands.create import _is_local_path
from briefcase.commands.open import OpenCommand
from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError, ParseError

DEFAULT_OUTPUT_FORMAT = "system"

DEBIAN = "debian"
RHEL = "rhel"
ARCH = "arch"
SUSE = "suse"


def parse_freedesktop_os_release(content):
    """Parse the content of an /etc/os-release file.

    Implementation adapted from Example 5 of
    https://www.freedesktop.org/software/systemd/man/os-release.html

    :param content: The text content of the /etc/os-release file.
    :returns: A dictionary of key-value pairs, in the same format returned by
        `platform.freedesktop_os_release()`.
    """
    values = {}
    for line_number, line in enumerate(content.split("\n"), start=1):
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"([A-Z][A-Z_0-9]+)=(.*)", line)
        if m:
            name, val = m.groups()
            if val and val[0] in "\"'":
                try:
                    val = ast.literal_eval(val)
                except SyntaxError as e:
                    raise ParseError(
                        "Failed to parse output of FreeDesktop os-release file; "
                        f"Line {line_number}: {e}"
                    ) from e
            values[name] = val
        else:
            raise ParseError(
                "Failed to parse output of FreeDesktop os-release file; "
                f"Line {line_number}: {line!r}"
            )

    return values


class LinuxMixin:
    platform = "linux"

    def support_package_url(self, support_revision):
        """The URL of the support package to use for apps of this type.

        Linux builds that use a support package (AppImage, Flatpak) use Astral's (nee
        indygreg's) Standalone Python to provide system packages. See
        `https://github.com/astral-sh/python-build-standalone` for details.

        System packages don't use a support package; this is defined by the template, so
        this method won't be invoked.
        """
        python_download_arch = self.tools.host_arch
        # use a 32bit Python if using 32bit Python on 64bit hardware
        if self.tools.is_32bit_python and self.tools.host_arch == "aarch64":
            python_download_arch = "armv7"
        elif self.tools.is_32bit_python and self.tools.host_arch == "x86_64":
            python_download_arch = "i686"

        _version, datestamp = support_revision.split("+")
        return (
            "https://github.com/astral-sh/python-build-standalone/releases/download/"
            f"{datestamp}/"
            f"cpython-{support_revision}-{python_download_arch}-unknown-linux-gnu-install_only_stripped.tar.gz"
        )

    def vendor_details(self, freedesktop_info):
        """Normalize the identity of the target Linux vendor, version, and base.

        :param freedesktop_info: The parsed content of the FreeDesktop /etc/os-release
            file. This is the same format returned by
            `platform.freedesktop_os_release()`.
        :returns: A tuple of (vendor, version, vendor_base).
        """
        vendor = freedesktop_info["ID"]
        try:
            codename = freedesktop_info["VERSION_CODENAME"]
            if not codename:
                # Fedora *has* a VERSION_CODENAME key, but it is empty.
                # Treat it as missing.
                raise KeyError("VERSION_CODENAME")
        except KeyError:
            try:
                # Arch uses a specific constant in VERSION_ID
                if freedesktop_info["VERSION_ID"] == "TEMPLATE_VERSION_ID":
                    codename = "rolling"
                else:
                    codename = freedesktop_info["VERSION_ID"].split(".")[0]
            except KeyError:
                # Manjaro doesn't have a VERSION_ID key
                codename = "rolling"

        # Process the vendor_base from the vendor.
        id_like = freedesktop_info.get("ID_LIKE", "").split()
        if vendor == DEBIAN or DEBIAN in id_like or "ubuntu" in id_like:
            vendor_base = DEBIAN
        elif vendor == RHEL or vendor == "fedora" or RHEL in id_like:
            vendor_base = RHEL
        elif vendor == ARCH or vendor == "cachyos" or ARCH in id_like:
            vendor_base = ARCH
        elif vendor == SUSE or SUSE in id_like:
            vendor_base = SUSE
        else:
            vendor_base = None

        return vendor, codename, vendor_base


class LocalRequirementsMixin:  # pragma: no-cover-if-is-windows
    # A mixin that captures the process of compiling requirements that are specified
    # as local file references into sdists, and then installing those requirements
    # from the sdist.

    def local_requirements_path(self, app):
        return self.bundle_path(app) / "_requirements"

    def _install_app_requirements(
        self,
        app: AppConfig,
        requires: list[str],
        app_packages_path: Path,
        **kwargs,
    ):
        """Install requirements for the app with pip.

        This method pre-compiles any requirement defined using a local path reference
        into an sdist tarball. This will be used when installing under Docker, as local
        file references can't be accessed in the Docker container.

        :param app: The app configuration
        :param requires: The list of requirements to install
        :param app_packages_path: The full path of the app_packages folder into which
            requirements should be installed.
        """
        # If we're re-building requirements, purge any pre-existing local
        # requirements.
        local_requirements_path = self.local_requirements_path(app)
        if local_requirements_path.exists():
            self.tools.shutil.rmtree(local_requirements_path)
        self.tools.os.mkdir(local_requirements_path)

        # Iterate over every requirement, looking for local references
        localized_requires = []
        for requirement in requires:
            if _is_local_path(requirement):
                parts = requirement.rsplit("[", 1)
                req_name = parts[0]
                try:
                    extras = f"[{parts[1]}"
                except IndexError:
                    extras = ""

                local_req = (self.base_path / req_name).resolve()
                if local_req.is_dir():
                    # Requirement is a filesystem reference
                    # Build a wheel for the local requirement
                    with self.console.wait_bar(f"Building wheels for {req_name}..."):
                        try:
                            self.tools.subprocess.check_output(
                                [
                                    sys.executable,
                                    "-X",
                                    "utf8",
                                    "-m",
                                    "build",
                                    "--wheel",
                                    "--outdir",
                                    local_requirements_path,
                                    local_req,
                                ],
                                encoding="UTF-8",
                            )

                            # The newest file in the directory will be the wheel that
                            # was just created.
                            newest_file = max(
                                (
                                    f
                                    for f in self.local_requirements_path(app).iterdir()
                                    if f.is_file()
                                ),
                                key=lambda f: f.stat().st_mtime,
                            )

                            localized_requires.append(str(newest_file) + extras)

                        except subprocess.CalledProcessError as e:
                            raise BriefcaseCommandError(
                                f"Unable to build wheel for {requirement}"
                            ) from e
                else:
                    try:
                        # Requirement is an existing sdist or wheel file.
                        self.tools.shutil.copy(local_req, local_requirements_path)

                        # The requirement must be re-written as a local file reference
                        localized_requires.append(
                            str(self.local_requirements_path(app) / local_req.name)
                            + extras
                        )

                    except OSError as e:
                        raise BriefcaseCommandError(
                            f"Unable to find local requirement {requirement}"
                        ) from e
            else:
                # The requirement can be used as-is
                localized_requires.append(requirement)

        # Continue with the default app requirement handling.
        return super()._install_app_requirements(
            app,
            requires=localized_requires,
            app_packages_path=app_packages_path,
        )


class DockerOpenCommand(OpenCommand):  # pragma: no-cover-if-is-windows
    # A command that redirects Open to an interactive shell in the container
    # if Docker is being used. Relies on the final command to provide
    # verification that Docker is available, and verify the app context.

    def _open_app(self, app: AppConfig):
        # If we're using Docker, open an interactive shell in the container.
        # Rely on the default CMD statement in the image's Dockerfile to
        # define a default shell.
        if self.use_docker:
            self.tools[app].app_context.run([], interactive=True)
        else:
            super()._open_app(app)
