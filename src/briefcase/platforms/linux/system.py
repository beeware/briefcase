import gzip
import os
import re
import subprocess
from pathlib import Path
from typing import List

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError, UnsupportedHostError
from briefcase.integrations.docker import Docker, DockerAppContext
from briefcase.integrations.subprocess import NativeAppContext
from briefcase.platforms.linux import (
    ARCH,
    DEBIAN,
    REDHAT,
    DockerOpenCommand,
    LinuxMixin,
    LocalRequirementsMixin,
)


class LinuxSystemPassiveMixin(LinuxMixin):
    # The Passive mixin honors the Docker options, but doesn't try to verify
    # Docker exists. It is used by commands that are "passive" from the
    # perspective of the build system (e.g., Run).
    output_format = "system"
    supported_host_os = {"Darwin", "Linux"}
    supported_host_os_reason = (
        "Linux system projects can only be built on Linux, or on macOS using Docker."
    )

    @property
    def use_docker(self):
        # The system backend doesn't have a literal "--use-docker" option, but
        # `use_docker` is a useful flag for shared logic purposes, so evaluate
        # what "use docker" means in terms of target_image.
        return bool(self.target_image)

    @property
    def linux_arch(self):
        # Linux uses different architecture identifiers for some platforms
        return {
            "x86_64": "amd64",
        }.get(self.tools.host_arch, self.tools.host_arch)

    def bundle_path(self, app):
        # Override the bundle path to use the app name, rather than formal name
        # This is because Red Hat doesn't like spaces in paths.
        return (
            self.platform_path / app.target_vendor / app.target_codename / app.app_name
        )

    def project_path(self, app):
        return self.bundle_path(app)

    def package_path(self, app):
        return self.bundle_path(app) / f"{app.app_name}-{app.version}"

    def binary_path(self, app):
        return self.package_path(app) / "usr" / "bin" / app.app_name

    def distribution_path(self, app):
        if app.packaging_format == "deb":
            return self.platform_path / (
                f"{app.app_name}_{app.version}-{getattr(app, 'revision', 1)}"
                f"~{app.target_vendor}-{app.target_codename}_{self.linux_arch}.deb"
            )
        else:
            raise BriefcaseCommandError(
                "Briefcase doesn't currently know how to build system packages in "
                f"{app.packaging_format.upper()} format."
            )

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "--target",
            dest="target",
            help="Docker base image tag for the distribution to target for the build (e.g., `ubuntu:jammy`)",
            required=False,
        )

    def parse_options(self, extra):
        """Extract the target_image option."""
        options = super().parse_options(extra)
        self.target_image = options.pop("target")

        return options

    def clone_options(self, command):
        """Clone the target_image option."""
        super().clone_options(command)
        self.target_image = command.target_image

    def target_glibc_version(self, app):
        """Determine the glibc version.

        If running in Docker, this is done by interrogating libc.so.6; outside
        docker, we can use os.confstr().
        """
        if self.use_docker:
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
                        "Unable to parse glibc dependency version from version string."
                    )
            except subprocess.CalledProcessError:
                raise BriefcaseCommandError(
                    "Unable to determine glibc dependency version."
                )

        else:
            target_glibc = self.tools.os.confstr("CS_GNU_LIBC_VERSION").split()[1]

        return target_glibc

    def finalize_app_config(self, app: AppConfig):
        """Finalize app configuration.

        Linux .deb app configurations are deeper than other platforms, because
        they need to include components that are dependent on the target vendor
        and codename. Those properties are extracted from command-line options.

        The final app configuration merges the target-specific configuration
        into the generic "linux.deb" app configuration, as well as setting the
        Python version.

        :param app: The app configuration to finalize.
        """
        self.logger.info("Finalizing application configuration...", prefix=app.app_name)
        if self.use_docker:
            # Preserve the target image on the command line as the app's target
            app.target_image = self.target_image

            # Ensure that the Docker base image is available.
            with self.input.wait_bar(
                f"Checking Docker target image {app.target_image}..."
            ):
                self.tools.docker.prepare(app.target_image)

            app.target_vendor, app.target_codename = app.target_image.split(":")

            # Manjaro uses `manjarolinux/base` as the image; RHEL uses
            # `redhat/ubi8`; so we can use anything before the / as the vendor.
            app.target_vendor = app.target_vendor.split("/")[0]
        else:
            app.target_vendor, app.target_codename = self.host_distribution()

            self.logger.info(f"Targeting {app.target_vendor}:{app.target_codename}")
            app.target_image = f"{app.target_vendor}:{app.target_codename}"

        # Determine the vendor base.
        app.target_vendor_base = self.vendor_base(app.target_vendor)

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
            for key, value in config.items():
                setattr(app, key, value)

        with self.input.wait_bar("Determining glibc version..."):
            app.glibc_version = self.target_glibc_version(app)
        self.logger.info(f"Targeting glibc {app.glibc_version}")

        if self.use_docker:
            # If we're running in Docker, we can't know the Python3 version
            # before rolling out the template; so we fall back to "3"
            app.python_version_tag = "3"
        else:
            # Use the version of Python that run
            app.python_version_tag = self.python_version_tag

        self.logger.info(f"Targeting Python{app.python_version_tag}")


class LinuxSystemMostlyPassiveMixin(LinuxSystemPassiveMixin):
    # The Mostly Passive mixin verifies that Docker exists and can be run, but
    # doesn't require that we're actually in a Linux environment.

    def docker_image_tag(self, app):
        """The Docker image tag for an app."""
        return f"briefcase/{app.bundle}.{app.app_name.lower()}:{app.target_vendor}-{app.target_codename}"

    def verify_tools(self):
        """If we're using Docker, verify that it is available."""
        super().verify_tools()
        if self.use_docker:
            Docker.verify(tools=self.tools)

    def verify_python(self, app):
        """Verify that the version of Python being used to build the app in Docker
        is compatible with the version being used to run Briefcase.

        Will raise an exception if the Python version is fundamentally
        incompatible (i.e., if Briefcase doesn't support it); any other version
        discrepancy will log a warning, but continue.

        Requires that the app tools have been verified.

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
        target_python_tag = output.split("\n")[0]
        target_python_version = tuple(int(v) for v in target_python_tag.split("."))[:2]

        if target_python_version < self.briefcase_required_python_version:
            briefcase_min_version = ".".join(
                str(v) for v in self.briefcase_required_python_version
            )
            raise BriefcaseCommandError(
                f"The system python3 version provided by {app.target_image} "
                f"is {target_python_tag}; Briefcase requires a "
                f"minimum Python3 version of {briefcase_min_version}."
            )
        elif target_python_version != (
            self.tools.sys.version_info.major,
            self.tools.sys.version_info.minor,
        ):
            self.logger.warning(
                f"""
*************************************************************************
** WARNING: Python version mismatch!                                   **
*************************************************************************

    The system python3 provided by {app.target_image} is {target_python_tag}.
    This is not the same as your local system ({self.python_version_tag}).

    Ensure you have tested for Python version compatibility before
    releasing this app.

*************************************************************************
"""
            )

    def verify_system_python(self):
        """Verify that the Python being used to run Briefcase is the
        default system python.

        Will raise an exception if the system Python isn't an obvious
        Python3, or the Briefcase Python isn't the same version as the
        system Python.

        Requires that the app tools have been verified.
        """
        system_python_bin = Path("/usr/bin/python3").resolve()
        system_version = system_python_bin.name.split(".")
        if system_version[0] != "python3" or len(system_version) == 1:
            raise BriefcaseCommandError("Can't determine the system python version")

        if system_version[1] != str(self.tools.sys.version_info.minor):
            raise BriefcaseCommandError(
                f"The version of Python being used to run Briefcase ({self.python_version_tag}) "
                f"is not the system python3 (3.{system_version[1]})."
            )

    def verify_app_tools(self, app: AppConfig):
        """Verify App environment is prepared and available.

        When Docker is used, create or update a Docker image for the App.
        Without Docker, the host machine will be used as the App environment.

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
                host_platform_path=self.platform_path,
                host_data_path=self.data_path,
                python_version=app.python_version_tag,
            )

            # Check the system Python on the target system to see if it is
            # compatible with Briefcase.
            if verify_python:
                self.verify_python(app)
        else:
            NativeAppContext.verify(tools=self.tools, app=app)

            # Check the system Python on the target system to see if it is
            # compatible with Briefcase.
            if verify_python:
                self.verify_system_python()

        # Establish Docker as app context before letting super set subprocess
        super().verify_app_tools(app)


class LinuxSystemMixin(LinuxSystemMostlyPassiveMixin):
    def verify_host(self):
        """If we're *not* using Docker, verify that we're actually on Linux."""
        super().verify_host()
        if not self.use_docker:
            if self.tools.host_os != "Linux":
                raise UnsupportedHostError(self.supported_host_os_reason)


class LinuxSystemCreateCommand(LinuxSystemMixin, LocalRequirementsMixin, CreateCommand):
    description = "Create and populate a Linux system project."

    def output_format_template_context(self, app: AppConfig):
        context = super().output_format_template_context(app)

        # The base template context includes the host Python version;
        # override that with an app-specific Python version, allowing
        # for the app to be built with the system Python.
        context["python_version"] = app.python_version_tag

        # Add the docker base image
        context["docker_base_image"] = app.target_image

        # Add the vendor base
        context["vendor_base"] = app.target_vendor_base

        return context

    def install_app_resources(self, app: AppConfig):
        """Install the application resources (such as icons and splash screens) into the
        bundle.

        :param app: The config object for the app
        """
        super().install_app_resources(app)

        with self.input.wait_bar("Installing copyright file..."):
            source_license_file = self.base_path / "LICENSE"
            license_file = self.bundle_path(app) / "LICENSE"
            if source_license_file.exists():
                self.tools.shutil.copy(source_license_file, license_file)
            else:
                self.logger.warning(
                    f"""
*************************************************************************
** WARNING: No LICENSE file!                                           **
*************************************************************************

    Your project does not contain a LICENSE file.

    Linux app packaging guidelines require that packages provide a
    copyright statement. A dummy LICENSE file ({license_file.relative_to(self.base_path)})
    has been created by the app template. You should ensure this file
    is complete and correct before continuing.

*************************************************************************
"""
                )

        with self.input.wait_bar("Installing changelog..."):
            source_changelog_file = self.base_path / "CHANGELOG"
            changelog_file = self.bundle_path(app) / "CHANGELOG"
            if source_changelog_file.exists():
                self.tools.shutil.copy(source_changelog_file, changelog_file)
            else:
                self.logger.warning(
                    f"""
*************************************************************************
** WARNING: No CHANGELOG file!                                         **
*************************************************************************

    Your project does not contain a CHANGELOG file.

    Linux app packaging guidelines require that packages provide a
    change log. A dummy CHANGELOG file ({changelog_file.relative_to(self.base_path)})
    has been created by the app template. You should ensure this file
    is complete and correct before continuing.

*************************************************************************
"""
                )


class LinuxSystemUpdateCommand(LinuxSystemCreateCommand, UpdateCommand):
    description = "Update an existing Linux system project."


class LinuxSystemOpenCommand(LinuxSystemMostlyPassiveMixin, DockerOpenCommand):
    description = (
        "Open a shell in a Docker container for an existing Linux system project."
    )


class LinuxSystemBuildCommand(LinuxSystemMixin, BuildCommand):
    description = "Build a Linux system project."

    def build_app(self, app: AppConfig, **kwargs):
        """Build an application.

        :param app: The application to build
        """
        self.logger.info("Building application...", prefix=app.app_name)

        self.logger.info("Build bootstrap binary...")
        with self.input.wait_bar("Building bootstrap binary..."):
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

        with self.input.wait_bar("Installing license..."):
            license_file = self.bundle_path(app) / "LICENSE"
            if license_file.exists():
                self.tools.shutil.copy(license_file, doc_folder / "copyright")
            else:
                raise BriefcaseCommandError("LICENSE source file is missing")

        with self.input.wait_bar("Installing changelog..."):
            changelog = self.bundle_path(app) / "CHANGELOG"
            if changelog.exists():
                with changelog.open() as infile:
                    outfile = gzip.GzipFile(
                        doc_folder / "changelog.gz", mode="wb", mtime=0
                    )
                    outfile.write(infile.read().encode("utf-8"))
                    outfile.close()
            else:
                raise BriefcaseCommandError("CHANGELOG source file is missing")

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

        with self.input.wait_bar("Installing man page..."):
            manpage_source = self.bundle_path(app) / f"{app.app_name}.1"
            if manpage_source.exists():
                with manpage_source.open() as infile:
                    outfile = gzip.GzipFile(
                        man_folder / f"{app.app_name}.1.gz", mode="wb", mtime=0
                    )
                    outfile.write(infile.read().encode("utf-8"))
                    outfile.close()
            else:
                raise BriefcaseCommandError(
                    f"manpage source file `{app.app_name}.1` is missing"
                )

        self.logger.info("Update file permissions...")
        with self.input.wait_bar("Updating file permissions..."):
            for path in self.package_path(app).glob("**/*"):
                old_perms = self.tools.os.stat(path).st_mode & 0o777
                user_perms = old_perms & 0o700
                world_perms = old_perms & 0o007

                # File permissions like 775 and 664 (where the group and user
                # permissions are the same), cause Debian heartburn. So, make
                # sure the group and world permissions are the same
                new_perms = user_perms | (world_perms << 3) | world_perms

                # If there's been any change in permissions, apply them
                if new_perms != old_perms:
                    self.logger.info(
                        "Updating file permissions on "
                        f"{path.relative_to(self.bundle_path(app))} "
                        f"from {oct(old_perms)[2:]} to {oct(new_perms)[2:]}"
                    )
                    path.chmod(new_perms)

        with self.input.wait_bar("Stripping binary..."):
            self.tools.subprocess.check_output(["strip", self.binary_path(app)])


class LinuxSystemRunCommand(LinuxSystemPassiveMixin, RunCommand):
    description = "Run a Linux system project."
    supported_host_os = {"Linux"}
    supported_host_os_reason = "Linux system projects can only be executed on Linux."

    def run_app(
        self, app: AppConfig, test_mode: bool, passthrough: List[str], **kwargs
    ):
        """Start the application.

        :param app: The config object for the app
        :param test_mode: Boolean; Is the app running in test mode?
        :param passthrough: The list of arguments to pass to the app
        """
        # Set up the log stream
        kwargs = self._prepare_app_env(app=app, test_mode=test_mode)

        # Start the app in a way that lets us stream the logs
        app_popen = self.tools.subprocess.Popen(
            [os.fsdecode(self.binary_path(app))] + passthrough,
            cwd=self.tools.home_path,
            **kwargs,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )

        # Start streaming logs for the app.
        self._stream_app_logs(
            app,
            popen=app_popen,
            test_mode=test_mode,
            clean_output=False,
        )


def debian_multiline_description(description):
    """Generate a Debian multiline description string.

    The long description in a Debian control file must
    *not* contain any blank lines, and each line must start with a single space.
    Convert a long description into Debian format.

    :param description: A multi-line long description string.
    :returns: A string in Debian's multiline format
    """
    return "\n ".join(line for line in description.split("\n") if line.strip() != "")


class LinuxSystemPackageCommand(LinuxSystemMixin, PackageCommand):
    description = "Package a Linux system project."

    @property
    def packaging_formats(self):
        return ["deb", "rpm", "pkg", "system"]

    def _verify_deb_tools(self):
        """Verify that the local environment contains the debian packaging tools."""
        if not Path("/usr/bin/dpkg-deb").exists():
            raise BriefcaseCommandError(
                "Can't find the dpkg tools. Try running `sudo apt install dpkg-dev`."
            )

    def verify_app_tools(self, app):
        super().verify_app_tools(app)
        # If "system" packaging format was selected, determine what that means.
        if app.packaging_format == "system":
            app.packaging_format = {
                DEBIAN: "deb",
                REDHAT: "rpm",
                ARCH: "pkg",
            }.get(app.target_vendor_base, None)

        if app.packaging_format is None:
            raise BriefcaseCommandError(
                "Briefcase doesn't know the system packaging format for "
                f"{app.target_vendor}. You may be able to build a package "
                "by manually specifying a format with -p/--packaging-format"
            )

        if not self.use_docker:
            # Check for the format-specific packaging tools.
            if app.packaging_format == "deb":
                self._verify_deb_tools()

    def package_app(self, app: AppConfig, **kwargs):
        if app.packaging_format == "deb":
            self._package_deb(app, **kwargs)
        else:
            raise BriefcaseCommandError(
                "Briefcase doesn't currently know how to build system packages in "
                f"{app.packaging_format.upper()} format."
            )

    def _package_deb(self, app: AppConfig, **kwargs):
        self.logger.info("Building .deb package...", prefix=app.app_name)

        # The long description *must* exist.
        if app.long_description is None:
            raise BriefcaseCommandError(
                "App configuration does not define `long_description`. "
                "Debian projects require a long description."
            )

        # Write the Debian metadata control file.
        with self.input.wait_bar("Write Debian package control file..."):
            if (self.package_path(app) / "DEBIAN").exists():
                self.tools.shutil.rmtree(self.package_path(app) / "DEBIAN")

            (self.package_path(app) / "DEBIAN").mkdir()

            # Add runtime package dependencies. App config has been finalized,
            # so this will be the target-specific definition, if one exists.
            # libc6 is added because lintian complains without it, even though
            # it's a dependency of the thing we *do* care about - python.
            system_runtime_requires = ", ".join(
                [
                    f"libc6 (>={app.glibc_version})",
                    f"python{app.python_version_tag}",
                ]
                + getattr(app, "system_runtime_requires", [])
            )

            with (self.package_path(app) / "DEBIAN" / "control").open(
                "w", encoding="utf-8"
            ) as f:
                f.write(
                    "\n".join(
                        [
                            f"Package: { app.app_name }",
                            f"Version: { app.version }",
                            f"Architecture: { self.linux_arch }",
                            f"Maintainer: { app.author } <{ app.author_email }>",
                            f"Homepage: { app.url }",
                            f"Description: { app.description }",
                            f" { debian_multiline_description(app.long_description) }",
                            f"Depends: { system_runtime_requires }",
                            f"Section: { getattr(app, 'system_section', 'utils') }",
                            "Priority: optional\n",
                        ]
                    )
                )

        with self.input.wait_bar("Building Debian package..."):
            try:
                # Build the dpkg.
                self.tools[app].app_context.run(
                    [
                        "dpkg-deb",
                        "--build",
                        "--root-owner-group",
                        f"{app.app_name}-{app.version}",
                    ],
                    check=True,
                    cwd=self.bundle_path(app),
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Error while building .deb package for {app.app_name}."
                ) from e

            # Move the deb file to its final location
            self.tools.shutil.move(
                self.bundle_path(app) / f"{app.app_name}-{app.version}.deb",
                self.distribution_path(app),
            )


class LinuxSystemPublishCommand(LinuxSystemMixin, PublishCommand):
    description = "Publish a Linux system project."


# Declare the briefcase command bindings
create = LinuxSystemCreateCommand  # noqa
update = LinuxSystemUpdateCommand  # noqa
open = LinuxSystemOpenCommand  # noqa
build = LinuxSystemBuildCommand  # noqa
run = LinuxSystemRunCommand  # noqa
package = LinuxSystemPackageCommand  # noqa
publish = LinuxSystemPublishCommand  # noqa
