from __future__ import annotations

import gzip
import re
import subprocess
from collections.abc import Collection
from pathlib import Path

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    DevCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.commands.convert import find_changelog_filename
from briefcase.config import AppConfig, merge_config
from briefcase.exceptions import BriefcaseCommandError, UnsupportedHostError
from briefcase.formats import get_packaging_format
from briefcase.integrations.docker import Docker, DockerAppContext
from briefcase.integrations.subprocess import NativeAppContext
from briefcase.integrations.virtual_environment import VenvContext
from briefcase.platforms.linux import (
    ARCH,
    DEBIAN,
    RHEL,
    SUSE,
    DockerOpenCommand,
    LinuxMixin,
    LocalRequirementsMixin,
    parse_freedesktop_os_release,
)


class LinuxSystemMixin(LinuxMixin):
    # The base mixin for system packages. It only supports native Linux usage, not usage
    # through Docker.
    output_format = "system"
    supports_external_packaging = True

    def build_path(self, app):
        # Override the default build path to use the vendor name,
        # rather than "linux"
        return self.base_path / "build" / app.app_name / app.target_vendor

    def bundle_path(self, app):
        # Override the default bundle path to use the codename,
        # rather than "system"
        return self.build_path(app) / app.target_codename

    def project_path(self, app):
        return self.bundle_path(app) / f"{app.app_name}-{app.version}"

    def binary_path(self, app):
        return self.project_path(app) / "usr/bin" / app.app_name

    def bundle_package_path(self, app):
        return self.project_path(app)

    def rpm_tag(self, app):
        if app.target_vendor == "fedora":
            return f"fc{app.target_codename}"
        else:
            return f"el{app.target_codename}"

    def _build_env_abi(self, app: AppConfig):
        """Retrieves the ABI the packaging system is targeting in the build env.

        Each packaging system uses different values to identify the exact ABI that
        describes the target environment...so just defer to the packaging system.
        """
        command = {
            "deb": ["dpkg", "--print-architecture"],
            "rpm": ["rpm", "--eval", "%_target_cpu"],
            "pkg": ["pacman-conf", "Architecture"],
        }[app.packaging_format]
        try:
            return (
                self.tools[app].app_context.check_output(command).split("\n")[0].strip()
            )
        except (OSError, subprocess.CalledProcessError) as e:
            raise BriefcaseCommandError(
                "Failed to determine build environment's ABI for packaging."
            ) from e

    def deb_abi(self, app: AppConfig) -> str:
        """The default ABI for dpkg packaging for the target environment."""
        try:
            return self._deb_abi
        except AttributeError:
            self._deb_abi = self._build_env_abi(app)
            return self._deb_abi

    def rpm_abi(self, app: AppConfig) -> str:
        """The default ABI for rpm packaging for the target environment."""
        try:
            return self._rpm_abi
        except AttributeError:
            self._rpm_abi = self._build_env_abi(app)
            return self._rpm_abi

    def pkg_abi(self, app: AppConfig) -> str:
        """The default ABI for pacman packaging for the target environment."""
        try:
            return self._pkg_abi
        except AttributeError:
            self._pkg_abi = self._build_env_abi(app)
            return self._pkg_abi

    def distribution_filename(self, app: AppConfig) -> str:
        if app.packaging_format == "deb":
            return (
                f"{app.bundle_name}"
                f"_{app.version}"
                f"-{getattr(app, 'revision', 1)}"
                f"~{app.target_vendor}"
                f"-{app.target_codename}"
                f"_{self.deb_abi(app)}"
                ".deb"
            )
        elif app.packaging_format == "rpm":
            # openSUSE doesn't include a distro tag
            if app.target_vendor_base == SUSE:
                distro_tag = ""
            else:
                distro_tag = f".{self.rpm_tag(app)}"
            return (
                f"{app.app_name}"
                f"-{app.version}"
                f"-{getattr(app, 'revision', 1)}"
                f"{distro_tag}"
                f".{self.rpm_abi(app)}"
                ".rpm"
            )
        elif app.packaging_format == "pkg":
            return (
                f"{app.app_name}"
                f"-{app.version}"
                f"-{getattr(app, 'revision', 1)}"
                f"-{self.pkg_abi(app)}"
                ".pkg.tar.zst"
            )
        else:
            raise BriefcaseCommandError(
                "Briefcase doesn't currently know how to build system packages in "
                f"{app.packaging_format.upper()} format."
            )

    def distribution_path(self, app: AppConfig):
        # Use the app-specific packaging format if it's been set;
        # otherwise, use the command-level packaging format.
        # If neither is set (e.g., during a create command), default to "deb".
        try:
            packaging_format = app.packaging_format
        except AttributeError:
            packaging_format = getattr(self, "packaging_format", "deb")

        return get_packaging_format(
            packaging_format,
            platform=self.platform,
            output_format=self.output_format,
            command=self,
        ).distribution_path(app)

    def target_glibc_version(self, app):
        target_glibc = self.tools.os.confstr("CS_GNU_LIBC_VERSION").split()[1]
        return target_glibc

    def app_python_version_tag(self, app):
        # Use the version of Python that was used to run Briefcase.
        return self.python_version_tag

    def platform_freedesktop_info(self, app):
        try:
            freedesktop_info = self.tools.platform.freedesktop_os_release()

        except OSError as e:
            raise BriefcaseCommandError(
                "Could not find the /etc/os-release file. "
                "Is this a FreeDesktop-compliant Linux distribution?"
            ) from e

        return freedesktop_info

    def _finalize_target_image(self, app: AppConfig):
        app.target_image = f"{app.target_vendor}:{app.target_codename}"

    def finalize_app_config(self, app: AppConfig):
        """Finalize app configuration.

        Linux .deb app configurations are deeper than other platforms, because they need
        to include components that are dependent on the target vendor and codename.
        Those properties are extracted from command-line options.

        The final app configuration merges the target-specific configuration into the
        generic "linux.deb" app configuration, as well as setting the Python version.

        :param app: The app configuration to finalize.
        """
        self.console.verbose(
            "Finalizing application configuration...", prefix=app.app_name
        )
        freedesktop_info = self.platform_freedesktop_info(app)

        # Process the FreeDesktop content to give the vendor, codename and vendor base.
        (
            app.target_vendor,
            app.target_codename,
            app.target_vendor_base,
        ) = self.vendor_details(freedesktop_info)

        self.console.verbose(
            f"Targeting {app.target_vendor}:{app.target_codename} "
            f"(Vendor base {app.target_vendor_base})"
        )

        # Finalize the target image being used by the app
        self._finalize_target_image(app)

        # Merge target-specific configuration items into the app config This
        # means:
        # * merging app.linux.debian into app, overwriting anything global
        # * merging app.linux.ubuntu into app, overwriting anything vendor-base
        #   specific
        # * merging app.linux.ubuntu.focal into app, overwriting anything vendor
        #   specific
        # The vendor base config (e.g., redhat). The vendor base might not
        # be known, so fall back to an empty vendor config.
        if app.target_vendor_base:
            vendor_base_config = getattr(app, app.target_vendor_base, {})
        else:
            vendor_base_config = {}
        vendor_config = getattr(app, app.target_vendor, {})
        try:
            codename_config = vendor_config[app.target_codename]
        except KeyError:
            codename_config = {}

        # Copy all the specific configurations to the app config
        for config in [
            vendor_base_config,
            vendor_config,
            codename_config,
        ]:
            merge_config(app, config)

        app.glibc_version = self.target_glibc_version(app)
        self.console.verbose(f"Targeting glibc {app.glibc_version}")

        app.python_version_tag = self.app_python_version_tag(app)

        self.console.verbose(f"Targeting Python{app.python_version_tag}")

    def _deb_devirtualize(self, package: str) -> str:
        """Convert a debian virtual package into a "real" package.

        Debian has the concept of "virtual" packages, where you can install one target,
        but another package is installed in practice, and the explicitly requested
        package is never shown in the installed list.

        A virtual package is identified as a package that defines a single `Reverse
        Provides` definition (although there may be multiple versions of that single
        package name), and doesn't have any `Provides` definitions. (e.g., `make`
        reverse-provides `make-guile`; but actually provides `make`, so it's not a
        virtual package; `mail-transport-agent` returns multiple *different*
        reverse-provides, so it can't be devirtualized).

        :param package: The possibly virtualized package name
        :returns: The devirtualized package name, or `None` if the package isn't
            a virtual package
        """
        devirtualized = None
        try:
            pkg_detail = self.tools.subprocess.check_output(
                ["apt-cache", "showpkg", package], quiet=1
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"""Unable to check apt-cache package record for {package!r}"""
            ) from e
        else:
            candidates = None
            for line in pkg_detail.split("\n"):
                if line == "Provides: ":
                    # If we hit a Provides line, start gathering package names
                    candidates = set()
                elif line == "Reverse Provides: ":
                    # Reverse Provides are listed after Provides. If the named package
                    # provides anything, it's not virtual, so reset the candidate list.
                    if candidates:
                        return None
                    else:
                        candidates = set()
                elif candidates is not None and line:
                    # Store the first part of the package name.
                    candidates.add(line.split(" ")[0])

            # If we've found exactly one candidate name, that's our actual package.
            if candidates is not None and len(candidates) == 1:
                devirtualized = next(iter(candidates))

        return devirtualized

    def _system_requirement_tools(self, app: AppConfig):
        """Utility method returning the packages and tools needed to verify system
        requirements.

        :param app: The app being built.
        :returns: A triple containing (0) The list of package names that must
            be installed at a bare minimum; (1) the arguments for the command
            used to verify the existence of a package on a system, and (2)
            the command used to install packages. All three values are `None`
            if the system cannot be identified.
        """
        if app.target_vendor_base == DEBIAN:
            base_system_packages = [
                "python3-dev",
                # The consitutent parts of build-essential
                ("dpkg-dev", "build-essential"),
                ("g++", "build-essential"),
                ("gcc", "build-essential"),
                ("libc6-dev", "build-essential"),
                ("make", "build-essential"),
            ]
            system_verify = ["dpkg", "-s"]
            system_devirtualize = self._deb_devirtualize
            system_installer = ["apt", "install"]
        elif app.target_vendor_base == RHEL:
            base_system_packages = [
                "python3-devel",
                "gcc",
                "make",
                "pkgconf-pkg-config",
            ]
            system_verify = ["rpm", "-q"]
            system_devirtualize = None
            system_installer = ["dnf", "install"]
        elif app.target_vendor_base == SUSE:
            base_system_packages = [
                "python3-devel",
                "patterns-devel-base-devel_basis",
            ]
            system_verify = ["rpm", "-q", "--whatprovides"]
            system_devirtualize = None
            system_installer = ["zypper", "install"]
        elif app.target_vendor_base == ARCH:
            base_system_packages = [
                "python3",
                "base-devel",
            ]
            system_verify = ["pacman", "-Q"]
            system_devirtualize = None
            system_installer = ["pacman", "-Syu"]
        else:
            base_system_packages = None
            system_verify = None
            system_devirtualize = None
            system_installer = None

        return (
            base_system_packages,
            system_devirtualize,
            system_verify,
            system_installer,
        )

    def verify_system_packages(self, app: AppConfig):
        """Verify that the required system packages are installed.

        Verifies both `system_requires` and `system_runtime_requires`.

        :param app: The app being built.
        """
        (
            base_system_packages,
            system_devirtualize,
            system_verify,
            system_installer,
        ) = self._system_requirement_tools(app)

        if not (system_verify and self.tools.shutil.which(system_verify[0])):
            self.console.warning("""
*************************************************************************
** WARNING: Can't verify system packages                               **
*************************************************************************

    Briefcase doesn't know how to verify the installation of system
    packages on your Linux distribution. If you have any problems
    building this app, ensure that the packages listed in the app's
    `system_requires` setting have been installed.

*************************************************************************
""")
            return

        # Run a check for each package listed in the app's system_requires,
        # plus the baseline system packages that are required.
        missing = set()
        verified = set()
        for package in (
            base_system_packages
            + getattr(app, "system_requires", [])
            + getattr(app, "system_runtime_requires", [])
        ):
            # Look for tuples in the package list. If there's a tuple, we're looking
            # for the first name in the tuple on the installed list, but we install
            # the package using the second name. This is to handle `build-essential`
            # style installation aliases. If it's not a tuple, the package name is
            # provided by the same name that we're checking for.
            if isinstance(package, tuple):
                installed, provided_by = package
            else:
                installed = provided_by = package

            if installed not in verified:
                verified.add(installed)
                try:
                    self.tools.subprocess.check_output(
                        [*system_verify, installed], quiet=1
                    )
                except subprocess.CalledProcessError:
                    # If the system uses devirtualization, try a devirtualized name
                    if system_devirtualize:
                        if devirtualized := system_devirtualize(installed):
                            try:
                                self.tools.subprocess.check_output(
                                    [*system_verify, devirtualized], quiet=1
                                )
                            except subprocess.CalledProcessError:
                                # Couldn't check devirtualized
                                missing.add(provided_by)
                        else:
                            # package isn't devirtualized
                            missing.add(provided_by)
                    else:
                        missing.add(provided_by)

        # If any required packages are missing, raise an error.
        if missing:
            raise BriefcaseCommandError(f"""\
Unable to build {app.app_name} due to missing system dependencies. Run:

    sudo {" ".join(system_installer)} {" ".join(sorted(missing))}

to install the missing dependencies, and re-run Briefcase.
""")


class LinuxSystemDockerMixin(LinuxSystemMixin):
    # Add options to allow the use of Docker.
    supported_host_os: Collection[str] = {"Darwin", "Linux"}
    supported_host_os_reason = (
        "Linux system projects can only be built on Linux, or on macOS using Docker."
    )

    @property
    def use_docker(self):
        # The system backend doesn't have a literal "--use-docker" option, but
        # `use_docker` is a useful flag for shared logic purposes, so evaluate
        # what "use docker" means in terms of target_image.
        return bool(self.target_image)

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "--target",
            dest="target",
            help=(
                "Docker base image tag for the distribution to target for the build "
                "(e.g., `ubuntu:jammy`)"
            ),
            required=False,
        )
        parser.add_argument(
            "--Xdocker-build",
            action="append",
            dest="extra_docker_build_args",
            help="Additional arguments to use when building the Docker image",
            required=False,
        )

    def parse_options(self, extra):
        """Extract the target_image option."""
        options, overrides = super().parse_options(extra)
        self.target_image = options.pop("target")
        self.extra_docker_build_args = options.pop("extra_docker_build_args")

        return options, overrides

    def app_python_version_tag(self, app: AppConfig):
        if self.use_docker:
            # If we're running in Docker, we can't know the Python3 version
            # before rolling out the template; so we fall back to "3". Later,
            # once we have a container in which we can run Python, this will be
            # updated to the actual Python version as part of the
            # `verify_python` app check.
            python_version_tag = "3"
        else:
            python_version_tag = super().app_python_version_tag(app)
        return python_version_tag

    def _finalize_target_image(self, app):
        if self.use_docker:
            # If we're using Docker, the target image is set by the --target command
            # line argument
            if app.external_package_path:
                raise BriefcaseCommandError(
                    "Briefcase can't currently use Docker to package "
                    "external apps as Linux system packages."
                )

            # If we're building for Arch, and Docker does user mapping, we can't build,
            # because Arch won't let makepkg run as root. Docker on macOS *does* map the
            # user, but introducing a step-down user doesn't alter behavior, so we can
            # allow it.
            if (
                app.target_vendor_base == ARCH
                and self.tools.docker.is_user_mapped
                and self.tools.host_os != "Darwin"
            ):
                raise BriefcaseCommandError("""\
Briefcase cannot use this Docker installation to target Arch Linux since the
tools to build packages for Arch cannot be run as root.

The Docker available to Briefcase requires the use of the root user in
containers to maintain accurate file permissions of the build artefacts.

This most likely means you're using Docker Desktop or rootless Docker.

Install Docker Engine and try again or run Briefcase on an Arch host system.
""")
        else:
            super()._finalize_target_image(app)

    def target_glibc_version(self, app):
        """Determine the glibc version.

        If running in Docker, this is done by interrogating libc.so.6; outside docker,
        we can use os.confstr().
        """
        if self.use_docker:
            with self.console.wait_bar("Determining glibc version..."):
                try:
                    output = self.tools.docker.check_output(
                        ["ldd", "--version"],
                        image_tag=app.target_image,
                    )
                    # On Debian/Ubuntu, ldd --version will give you output of the form:
                    #
                    #     ldd (Ubuntu GLIBC 2.31-0ubuntu9.9) 2.31
                    #     Copyright (C) 2020 Free Software Foundation, Inc.
                    #     ...
                    #
                    # Other platforms produce output of the form:
                    #
                    #     ldd (GNU libc) 2.36
                    #     Copyright (C) 2020 Free Software Foundation, Inc.
                    #     ...
                    #
                    # Note that the exact text will vary version to version.
                    # Look for the "2.NN" pattern.
                    if match := re.search(r"\d\.\d+", output):
                        target_glibc = match.group(0)
                    else:
                        raise BriefcaseCommandError(
                            "Unable to parse glibc dependency version from version"
                            " string."
                        )
                except subprocess.CalledProcessError as e:
                    raise BriefcaseCommandError(
                        "Unable to determine glibc dependency version."
                    ) from e

        else:
            target_glibc = super().target_glibc_version(app)

        return target_glibc

    def platform_freedesktop_info(self, app: AppConfig):
        if self.use_docker:
            # Preserve the target image on the command line as the app's target
            app.target_image = self.target_image

            # Extract release information from the image.
            with self.console.wait_bar(
                f"Checking Docker target image {app.target_image}..."
            ):
                output = self.tools.docker.check_output(
                    ["cat", "/etc/os-release"],
                    image_tag=app.target_image,
                )
                freedesktop_info = parse_freedesktop_os_release(output)
        else:
            freedesktop_info = super().platform_freedesktop_info(app)

        return freedesktop_info

    def docker_image_tag(self, app: AppConfig):
        """The Docker image tag for an app."""
        return (
            f"briefcase/{app.bundle_identifier.lower()}:"
            f"{app.target_vendor}-{app.target_codename}"
        )

    def verify_host(self):
        """If we're *not* using Docker, verify that we're actually on Linux."""
        super().verify_host()
        if not self.use_docker and self.tools.host_os != "Linux":
            raise UnsupportedHostError(self.supported_host_os_reason)

    def verify_tools(self):
        """If we're using Docker, verify that it is available."""
        super().verify_tools()
        if self.use_docker:
            Docker.verify(tools=self.tools, image_tag=self.target_image)

    def clone_options(self, command):
        """Clone the target_image option."""
        super().clone_options(command)
        self.target_image = command.target_image
        self.extra_docker_build_args = command.extra_docker_build_args

    def verify_docker_python(self, app: AppConfig):
        """Verify that the version of Python being used to build the app in Docker is
        compatible with the version being used to run Briefcase.

        Will raise an exception if the Python version is fundamentally
        incompatible (i.e., if Briefcase doesn't support it); any other version
        discrepancy will log a warning, but continue.

        Requires that the app tools have been verified.

        As a side effect of verifying Python, the `python_version_tag` will be
        updated to reflect the *actual* python version, not just a generic "3".

        :param app: The application being built
        """
        output = self.tools[app].app_context.check_output(
            [
                f"python{app.python_version_tag}",
                "-c",
                (
                    "import sys; "
                    "print(f'{sys.version_info.major}.{sys.version_info.minor}')"
                ),
            ]
        )
        # Update the python version tag with the *actual* python version.
        app.python_version_tag = output.split("\n")[0]
        target_python_version = tuple(int(v) for v in app.python_version_tag.split("."))

        if target_python_version < self.briefcase_required_python_version:
            briefcase_min_version = ".".join(
                str(v) for v in self.briefcase_required_python_version
            )
            raise BriefcaseCommandError(
                f"The system python3 version provided by {app.target_image} "
                f"is {app.python_version_tag}; Briefcase requires a "
                f"minimum Python3 version of {briefcase_min_version}."
            )
        elif target_python_version != (
            self.tools.sys.version_info.major,
            self.tools.sys.version_info.minor,
        ):
            self.console.warning(f"""
*************************************************************************
** WARNING: Python version mismatch!                                   **
*************************************************************************

    The system python3 provided by {app.target_image} is {app.python_version_tag}.
    This is not the same as your local system ({self.python_version_tag}).

    Ensure you have tested for Python version compatibility before
    releasing this app.

*************************************************************************
""")

    def verify_system_python(self):
        """Verify that the Python being used to run Briefcase is the default system
        python.

        Will raise an exception if the system Python isn't an obvious Python3, or the
        Briefcase Python isn't the same version as the system Python.

        Requires that the app tools have been verified.
        """
        system_python_bin = Path("/usr/bin/python3")
        if not system_python_bin.exists():
            raise BriefcaseCommandError(
                "Can't determine the system python version "
                "('/usr/bin/python3' does not exist)"
            )

        running_version = self.tools.sys.version
        system_version = self.tools.subprocess.check_output(
            [system_python_bin, "-c", "import sys; print(sys.version)"]
        ).strip()

        if system_version != running_version:
            raise BriefcaseCommandError(
                "The version of Python being used to run Briefcase "
                f"({running_version!r}) is not the system python3 "
                f"({system_version!r})."
            )

    def verify_app_tools(self, app: AppConfig):
        """Verify App environment is prepared and available.

        When Docker is used, create or update a Docker image for the App. Without
        Docker, the host machine will be used as the App environment.

        :param app: The application being built
        """
        # Verifying the App context is idempotent; but we have some
        # additional logic that we only want to run the first time through.
        # Check (and store) the pre-verify app tool state.
        verify_python = not hasattr(self.tools[app], "app_context")

        if self.use_docker:
            DockerAppContext.verify(
                tools=self.tools,
                app=app,
                image_tag=self.docker_image_tag(app),
                dockerfile_path=self.bundle_path(app) / "Dockerfile",
                app_base_path=self.base_path,
                host_bundle_path=self.bundle_path(app),
                host_data_path=self.data_path,
                python_version=app.python_version_tag,
                extra_build_args=self.extra_docker_build_args,
            )

            # Check the system Python on the target system to see if it is
            # compatible with Briefcase.
            if verify_python:
                self.verify_docker_python(app)
        else:
            NativeAppContext.verify(tools=self.tools, app=app)

            # Check the system Python on the target system to see if it is
            # compatible with Briefcase, and that the required system packages
            # are installed.
            if verify_python:
                self.verify_system_python()
                self.verify_system_packages(app)

        # Establish Docker as app context before letting super set subprocess
        super().verify_app_tools(app)


class LinuxSystemCreateCommand(
    LinuxSystemDockerMixin, LocalRequirementsMixin, CreateCommand
):
    description = "Create and populate a Linux system project."

    def output_format_template_context(self, app: AppConfig):
        context = super().output_format_template_context(app)

        # Linux system templates use the target codename, rather than
        # the format "system" as the leaf of the bundle path
        context["format"] = app.target_codename

        # The base template context includes the host Python version;
        # override that with an app-specific Python version, allowing
        # for the app to be built with the system Python.
        context["python_version"] = app.python_version_tag

        # Add the docker base image
        context["docker_base_image"] = app.target_image

        # Add the vendor base
        context["vendor_base"] = app.target_vendor_base

        # Use the non-root user if Docker is not mapping usernames. Also use a non-root
        # user if we're on macOS; user mapping doesn't alter Docker operation, but some
        # packaging tools (e.g., Arch's makepkg) don't like running as root. If we're
        # not using Docker, this will fall back to the template default, which should be
        # enabling the root user. This might cause problems later, but it's part of a
        # much bigger "does the project need to be updated in light of configuration
        # changes" problem.
        try:
            context["use_non_root_user"] = (
                self.tools.host_os == "Darwin" or not self.tools.docker.is_user_mapped
            )
        except AttributeError:
            pass  # ignore if not using Docker

        return context


class LinuxSystemUpdateCommand(LinuxSystemCreateCommand, UpdateCommand):
    description = "Update an existing Linux system project."


class LinuxSystemOpenCommand(LinuxSystemDockerMixin, DockerOpenCommand):
    description = (
        "Open a shell in a Docker container for an existing Linux system project."
    )


class LinuxSystemBuildCommand(LinuxSystemDockerMixin, BuildCommand):
    description = "Build a Linux system project."

    def build_app(self, app: AppConfig, **kwargs):
        """Build an application.

        :param app: The application to build
        """
        self.console.info("Building application...", prefix=app.app_name)

        self.console.info("Build bootstrap binary...")
        with self.console.wait_bar("Building bootstrap binary..."):
            try:
                # Build the bootstrap binary.
                self.tools[app].app_context.run(
                    [
                        "make",
                        "-C",
                        "bootstrap",
                        "install",
                    ],
                    check=True,
                    cwd=self.bundle_path(app),
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Error building bootstrap binary for {app.app_name}."
                ) from e

        # Make the folder for docs
        doc_folder = (
            self.bundle_path(app)
            / f"{app.app_name}-{app.version}"
            / "usr"
            / "share"
            / "doc"
            / app.app_name
        )
        doc_folder.mkdir(parents=True, exist_ok=True)

        if app.license_files:
            with self.console.wait_bar("Installing license..."):
                separator = "-" * 75
                parts = []
                for license_path_str in app.license_files:
                    parts.append(
                        (self.base_path / license_path_str).read_text(encoding="utf-8")
                    )
                (doc_folder / "copyright").write_text(
                    f"\n{separator}\n".join(parts), encoding="utf-8"
                )
        else:
            raise BriefcaseCommandError("""\
Your project does not include any license files.

Ensure your `pyproject.toml` is in PEP 639 format and specifies at least
one file in the `license-files` setting.
 """)

        with self.console.wait_bar("Installing changelog..."):
            changelog = find_changelog_filename(self.base_path)

            if changelog is None:
                raise BriefcaseCommandError("""\
Your project does not contain a changelog file with a known file name. You
must provide a changelog file in the same directory as your `pyproject.toml`,
with a known changelog file name (one of 'CHANGELOG', 'HISTORY', 'NEWS' or
'RELEASES'; the file may have an extension of '.md', '.rst', or '.txt', or have
no extension).
""")

            changelog_source = self.base_path / changelog

            with changelog_source.open(encoding="utf-8") as infile:
                outfile = gzip.GzipFile(doc_folder / "changelog.gz", mode="wb", mtime=0)
                outfile.write(infile.read().encode("utf-8"))
                outfile.close()

        # Make a folder for manpages
        man_folder = (
            self.bundle_path(app)
            / f"{app.app_name}-{app.version}"
            / "usr"
            / "share"
            / "man"
            / "man1"
        )
        man_folder.mkdir(parents=True, exist_ok=True)

        with self.console.wait_bar("Installing man page..."):
            manpage_source = self.bundle_path(app) / f"{app.app_name}.1"
            if manpage_source.is_file():
                with manpage_source.open(encoding="utf-8") as infile:
                    outfile = gzip.GzipFile(
                        man_folder / f"{app.app_name}.1.gz", mode="wb", mtime=0
                    )
                    outfile.write(infile.read().encode("utf-8"))
                    outfile.close()
            else:
                raise BriefcaseCommandError(
                    "Template does not provide a manpage source file "
                    f"`{app.app_name}.1`"
                )

        self.console.verbose("Update file permissions...")
        with self.console.wait_bar("Updating file permissions..."):
            for path in self.project_path(app).glob("**/*"):
                old_perms = self.tools.os.stat(path).st_mode & 0o777
                user_perms = old_perms & 0o700
                world_perms = old_perms & 0o007

                # File permissions like 775 and 664 (where the group and user
                # permissions are the same), cause Debian heartburn. So, make
                # sure the group and world permissions are the same
                new_perms = user_perms | (world_perms << 3) | world_perms

                # If there's been any change in permissions, apply them
                if new_perms != old_perms:  # pragma: no-cover-if-is-windows
                    self.console.verbose(
                        "Updating file permissions on "
                        f"{path.relative_to(self.bundle_path(app))} "
                        f"from {old_perms:o} to {new_perms:o}"
                    )
                    path.chmod(new_perms)

        with self.console.wait_bar("Stripping binary..."):
            self.tools.subprocess.check_output(["strip", self.binary_path(app)])


class LinuxSystemRunCommand(LinuxSystemDockerMixin, RunCommand):
    description = "Run a Linux system project."
    supported_host_os: Collection[str] = {"Linux"}
    supported_host_os_reason = "Linux system projects can only be executed on Linux."

    def run_app(
        self,
        app: AppConfig,
        passthrough: list[str],
        **kwargs,
    ):
        """Start the application.

        :param app: The config object for the app
        :param passthrough: The list of arguments to pass to the app
        """
        # Set up the log stream
        kwargs = self._prepare_app_kwargs(app=app)

        with self.tools[app].app_context.run_app_context(kwargs) as kwargs:
            # Console apps must operate in non-streaming mode so that console input can
            # be handled correctly. However, if we're in test mode, we *must* stream so
            # that we can see the test exit sentinel
            if app.console_app and not app.test_mode:
                self.console.info("=" * 75)
                self.tools[app].app_context.run(
                    [self.binary_path(app), *passthrough],
                    cwd=self.tools.home_path,
                    bufsize=1,
                    stream_output=False,
                    **kwargs,
                )
            else:
                # Start the app in a way that lets us stream the logs
                app_popen = self.tools[app].app_context.Popen(
                    [self.binary_path(app), *passthrough],
                    cwd=self.tools.home_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1,
                    **kwargs,
                )

                # Start streaming logs for the app.
                self._stream_app_logs(
                    app,
                    popen=app_popen,
                    clean_output=False,
                )


class LinuxSystemDevCommand(LinuxSystemMixin, DevCommand):
    description = "Run a Linux system app in development mode"
    supported_host_os_reason = "Linux system dev mode is only supported on Linux."

    def install_dev_requirements(self, app: AppConfig, venv: VenvContext, **options):
        """Install the requirements into the dev environment.

        This also verifies that the system packages have been installed. This is to
        ensure that any dependencies exist before installing wheels that might need to
        be compiled (e.g., PyGOobject requires compiler tooling and system GTK
        packages).
        """
        self.verify_system_packages(app)
        super().install_dev_requirements(app, venv, **options)


class LinuxSystemPackageCommand(LinuxSystemDockerMixin, PackageCommand):
    description = "Package a Linux system project for distribution."

    def _verify_packaging_tools(self, app: AppConfig):
        """Verify that the local environment contains the packaging tools."""
        tool_name, executable_name, package_name = {
            "deb": ("dpkg", "dpkg-deb", "dpkg-dev"),
            "rpm": ("rpm-build", "rpmbuild", "rpm-build"),
            "pkg": ("makepkg", "makepkg", "pacman"),
        }[app.packaging_format]

        if not self.tools.shutil.which(executable_name):
            if install_cmd := self._system_requirement_tools(app)[3]:
                raise BriefcaseCommandError(
                    f"Can't find the {tool_name} tools. "
                    f"Try running `sudo {' '.join(install_cmd)} {package_name}`."
                )
            else:
                raise BriefcaseCommandError(
                    f"Can't find the {executable_name} tool. "
                    f"Install this first to package the {app.packaging_format}."
                )

    def verify_app_tools(self, app):
        super().verify_app_tools(app)
        # If "system" packaging format was selected, determine what that means.
        if app.packaging_format == "system":
            app.packaging_format = {
                DEBIAN: "deb",
                RHEL: "rpm",
                ARCH: "pkg",
                SUSE: "rpm",
            }.get(app.target_vendor_base)

        if app.packaging_format is None:
            raise BriefcaseCommandError(
                "Briefcase doesn't know the system packaging format for "
                f"{app.target_vendor}. You may be able to build a package "
                "by manually specifying a format with -p/--packaging-format"
            )

        if not self.use_docker:
            self._verify_packaging_tools(app)


class LinuxSystemPublishCommand(LinuxSystemDockerMixin, PublishCommand):
    description = "Publish a Linux system project."


# Declare the briefcase command bindings
create = LinuxSystemCreateCommand
update = LinuxSystemUpdateCommand
open = LinuxSystemOpenCommand
build = LinuxSystemBuildCommand
run = LinuxSystemRunCommand
package = LinuxSystemPackageCommand
publish = LinuxSystemPublishCommand
dev = LinuxSystemDevCommand
