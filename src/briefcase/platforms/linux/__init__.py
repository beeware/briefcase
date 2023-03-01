import subprocess
import sys
from pathlib import Path
from typing import List

from briefcase.commands.create import _is_local_requirement
from briefcase.commands.open import OpenCommand
from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError

DEFAULT_OUTPUT_FORMAT = "system"

DEBIAN = "debian"
REDHAT = "redhat"
ARCH = "archlinux"


class LinuxMixin:
    platform = "linux"

    def _release_details(self, filename):
        """Read an /etc/X-release file.

        :param filename: The name of a file in the `/etc` folder
        :returns: The string content of the release file, or None if the file
            does not exist.
        """
        path = Path("/etc") / filename
        if path.exists():
            with path.open(encoding="utf-8") as f:
                return f.read()
        return None

    def host_distribution(self):
        """Identify the local Linux distribution and version.

        :returns: A tuple of (vendor, version).
        """
        # Try to identify the local Linux system
        # * Arch provides `/etc/arch-release`.
        # * Manjaro is an Arch derivative, and puts identifying content in
        #   `/etc/arch-release`
        # * Redhat-derived distros all provide `/etc/redhat-release`
        # * Fedora also provides `/etc/fedora-release`, which contains the
        #   version number
        # * Almalinux also provides `/etc/almalinux-release`, which contains the
        #   version number
        # * Debian-based distros use `lsb_release`; this *may* be present on
        #   other distros, but usage of code names is wierd (e.g., Fedora 34 has
        #   a code name "thirtyfour", but the docker image isn't tagged with
        #   that code name)
        if redhat_details := self._release_details("redhat-release"):
            if fedora_details := self._release_details("fedora-release"):
                # Parse "34" from "Fedora release 34 (thirtyfour)"
                vendor = "fedora"
                try:
                    version = fedora_details.split(" ")[2]
                except IndexError:
                    raise BriefcaseCommandError(
                        "Unable to parse Fedora release from /etc/fedora-release."
                    )
            elif centos_details := self._release_details("centos-release"):
                # Parse "8" from "CentOS Linux release 8.4.2105"
                vendor = "centos"
                try:
                    version = centos_details.split(" ")[3].split(".")[0]
                except IndexError:
                    raise BriefcaseCommandError(
                        "Unable to parse Centos release from /etc/centos-release."
                    )
            elif almalinux_details := self._release_details("almalinux-release"):
                # Parse "8" from "AlmaLinux release 8.7 (Stone Smilodon)"
                vendor = "almalinux"
                try:
                    version = almalinux_details.split(" ")[2].split(".")[0]
                except IndexError:
                    raise BriefcaseCommandError(
                        "Unable to parse AlmaLinux release "
                        "from /etc/almalinux-release content."
                    )
            else:
                # Parse "8" from "Red Hat Enterprise Linux release 8.7 (Ootpa)"
                vendor = "redhat"
                try:
                    version = redhat_details.split(" ")[5].split(".")[0]
                except IndexError:
                    raise BriefcaseCommandError(
                        "Unable to parse Red Hat Enterprise Linux release "
                        "from /etc/redhat-release content."
                    )

        elif (arch_details := self._release_details("arch-release")) is not None:
            if arch_details.startswith("Manjaro"):
                # Manjaro puts "Manjaro Linux" in /etc/arch-release
                vendor = "manjarolinux"
            elif not arch_details:
                # Arch is identified by *not* having anything in the
                # /etc/arch-release file
                vendor = "archlinux"
            else:
                raise BriefcaseCommandError(
                    "Unable to identify the specific arch-based Linux distribution "
                    "from /etc/arch-release content."
                )

            # Arch derivatives don't really have the concept of versions;
            # use "latest" as the codename.
            version = "latest"

        else:
            try:
                vendor = (
                    self.tools.subprocess.check_output(["lsb_release", "-i", "-s"])
                    .strip()
                    .lower()
                )
                version = (
                    self.tools.subprocess.check_output(["lsb_release", "-c", "-s"])
                    .strip()
                    .lower()
                )
            except subprocess.CalledProcessError:
                raise BriefcaseCommandError(
                    "Unable to identify the vendor of your Linux system using `lsb_release`."
                )

        return vendor, version

    def vendor_base(self, vendor):
        """Determine the base vendor type for the identified vendor.

        This is used to determine the package type used by the system.
        For example, Ubuntu has a base vendor of Debian; Fedora has a
        base vendor of Redhat.

        :param vendor: The vendor of the distribution
        :returns: The base vendor type; None if no vendor type can be identified.
        """
        # Derive the base vendor type for the specific vendor being targeted.
        if vendor in {"debian", "ubuntu", "linuxmint", "pop"}:
            base = DEBIAN
        elif vendor in {"redhat", "fedora", "centos", "almalinux"}:
            base = REDHAT
        elif vendor in {"archlinux", "manjarolinux"}:
            base = ARCH
        else:
            base = None
        return base


class LocalRequirementsMixin:
    # A mixin that captures the process of compiling requirements that are specified
    # as local file references into sdists, and then installing those requirements
    # from the sdist.

    def local_requirements_path(self, app):
        return self.bundle_path(app) / "_requirements"

    def _install_app_requirements(
        self,
        app: AppConfig,
        requires: List[str],
        app_packages_path: Path,
    ):
        """Install requirements for the app with pip.

        This method pre-compiles any requirement defined using a local path
        reference into an sdist tarball. This will be used when installing under
        Docker, as local file references can't be accessed in the Docker
        container.

        :param app: The app configuration
        :param requires: The list of requirements to install
        :param app_packages_path: The full path of the app_packages folder into
            which requirements should be installed.
        """
        # If we're re-building requirements, purge any pre-existing local
        # requirements.
        local_requirements_path = self.local_requirements_path(app)
        if local_requirements_path.exists():
            self.tools.shutil.rmtree(local_requirements_path)
        self.tools.os.mkdir(local_requirements_path)

        # Iterate over every requirements, looking for local references
        for requirement in requires:
            if _is_local_requirement(requirement):
                if Path(requirement).is_dir():
                    # Requirement is a filesystem reference
                    # Build an sdist for the local requirement
                    with self.input.wait_bar(f"Building sdist for {requirement}..."):
                        try:
                            self.tools.subprocess.check_output(
                                [
                                    sys.executable,
                                    "-m",
                                    "build",
                                    "--sdist",
                                    "--outdir",
                                    local_requirements_path,
                                    requirement,
                                ],
                            )
                        except subprocess.CalledProcessError as e:
                            raise BriefcaseCommandError(
                                f"Unable to build sdist for {requirement}"
                            ) from e
                else:
                    try:
                        # Requirement is an existing sdist or wheel file.
                        self.tools.shutil.copy(requirement, local_requirements_path)
                    except FileNotFoundError as e:
                        raise BriefcaseCommandError(
                            f"Unable to find local requirement {requirement}"
                        ) from e

        # Continue with the default app requirement handling.
        return super()._install_app_requirements(
            app,
            requires=requires,
            app_packages_path=app_packages_path,
        )

    def _pip_requires(self, app: AppConfig, requires: List[str]):
        """Convert the requirements list to an .deb project compatible format.

        Any local file requirements are converted into a reference to the file
        generated by _install_app_requirements().

        :param app: The app configuration
        :param requires: The user-specified list of app requirements
        :returns: The final list of requirement arguments to pass to pip
        """
        # Copy all the requirements that are non-local
        final = [
            requirement
            for requirement in super()._pip_requires(app, requires)
            if not _is_local_requirement(requirement)
        ]

        # Add in any local packages.
        # The sort is needed to ensure testing consistency
        for filename in sorted(self.local_requirements_path(app).iterdir()):
            final.append(filename)

        return final


class DockerOpenCommand(OpenCommand):
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
