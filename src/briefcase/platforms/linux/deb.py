import gzip
import itertools
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    OpenCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.commands.create import _is_local_requirement
from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError, UnsupportedHostError
from briefcase.integrations.docker import Docker, DockerAppContext
from briefcase.integrations.subprocess import NativeAppContext
from briefcase.platforms.linux import LinuxMixin

# Some constants defining known Python sources
SYSTEM = "system"
DEADSNAKES = "deadsnakes"


class LinuxDebPassiveMixin(LinuxMixin):
    # The Passive mixin honors the Docker options, but doesn't try to verify
    # Docker exists. It is used by commands that are "passive" from the
    # perspective of the build system (e.g., Run).
    output_format = "deb"
    supported_host_os = {"Darwin", "Linux"}
    supported_host_os_reason = (
        "Linux .deb projects can only be built on Linux, or on macOS using Docker."
    )

    @property
    def deb_arch(self):
        # Linux/Debian uses different architecture identifiers for some platforms
        return {
            "x86_64": "amd64",
        }.get(self.tools.host_arch, self.tools.host_arch)

    def python_source_tag(self, app):
        if app.python_source == SYSTEM:
            return "system"
        elif app.python_source == DEADSNAKES:
            return f"deadsnakes-py{app.python_version_tag}"

    def bundle_path(self, app):
        # The bundle path is different as there won't be a single "deb" build;
        # there is one per build target.
        return (
            self.platform_path
            / app.target_vendor
            / app.target_codename
            / self.python_source_tag(app)
            / app.formal_name
        )

    def project_path(self, app):
        return self.bundle_path(app)

    def package_path(self, app):
        return self.project_path(app) / self.package_name(app)

    def package_name(self, app):
        return f"{app.app_name}_{app.version}-{getattr(app, 'revision', 1)}_{self.deb_arch}"

    def local_requirements_path(self, app):
        return self.bundle_path(app) / "_requirements"

    def binary_path(self, app):
        return self.package_path(app) / "usr" / "bin" / app.app_name

    def distribution_path(self, app, packaging_format):
        return self.platform_path / (
            f"{app.app_name}_{app.version}-{getattr(app, 'revision', 1)}"
            f"~{app.target_vendor}-{app.target_codename}_{self.deb_arch}.deb"
        )

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "--target",
            dest="target",
            help="Debian-based distribution to target for the build (e.g., `ubuntu:jammy`)",
            required=False,
        )

    def parse_options(self, extra):
        """Extract the use_docker and target_image options."""
        options = super().parse_options(extra)
        self.target_image = options.pop("target")
        # If a target image is specified, we *must* be using docker.
        self.use_docker = self.target_image is not None

        return options

    def clone_options(self, command):
        """Clone the use_docker and target_image options."""
        super().clone_options(command)
        self.use_docker = command.use_docker
        self.target_image = command.target_image

    def target_glibc_version(self, app):
        """Determine the glibc version.

        If running in Docker, this is done by interrogating libc.so.6; outside
        docker, we can use os.confstr().
        """
        if self.use_docker:
            try:
                output = self.tools.docker.check_output(
                    app.target_image, ["ldd", "--version"]
                )
                # ldd --version will give you output of the form:
                #
                #     ldd (Ubuntu GLIBC 2.31-0ubuntu9.9) 2.31
                #     Copyright (C) 2020 Free Software Foundation, Inc.
                #     ...
                #
                # Note that the exact text will vary version to version; but the
                # "GLIBC 2.31-" part appears to be constant. From that first line,
                # we can parse the "2.31" that is the libc version.
                match = re.search(r" GLIBC (\d\.\d+)-", output)

                if match:
                    target_glibc = match[1]
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
        if self.target_image:
            # Preserve the target image on the command line as the app's target
            app.target_image = self.target_image

            # Ensure that the Docker base image is available.
            with self.input.wait_bar(
                f"Checking Docker target image {app.target_image}..."
            ):
                self.tools.docker.prepare(app.target_image)

            app.target_vendor, app.target_codename = app.target_image.split(":")

        else:
            app.target_vendor = (
                self.tools.subprocess.check_output(["lsb_release", "-i", "-s"])
                .strip()
                .lower()
            )
            app.target_codename = (
                self.tools.subprocess.check_output(["lsb_release", "-c", "-s"])
                .strip()
                .lower()
            )

            self.logger.info(f"Targeting {app.target_vendor}:{app.target_codename}")
            app.target_image = f"{app.target_vendor}:{app.target_codename}"

        # Merge target-specific configuration items into the app config
        try:
            target_config = getattr(app, app.target_vendor)[app.target_codename]
            for key, value in target_config.items():
                setattr(app, key, value)
        except (AttributeError, KeyError):
            pass

        with self.input.wait_bar("Determinining glibc version..."):
            app.glibc_version = self.target_glibc_version(app)
        self.logger.info(f"Targeting glibc {app.glibc_version}")

        # Determine the python source, and set the Python version tag as
        # appropriate. System Python uses a generic "3"; others use the specific
        # Python version that has been used to invoke Briefcase.
        try:
            if app.python_source == DEADSNAKES:
                if app.target_vendor != "ubuntu":
                    raise BriefcaseCommandError(
                        "Deadsnakes can only be used to build Ubuntu packages."
                    )
            elif app.python_source != SYSTEM:
                raise BriefcaseCommandError(
                    f"Unknown python source {app.python_source!r}; "
                    f"should be one of {SYSTEM!r}, {DEADSNAKES!r}"
                )
        except AttributeError:
            # python_source not defined; fall back to system.
            app.python_source = SYSTEM

        if app.python_source == SYSTEM:
            app.python_version_tag = "3"
        else:
            app.python_version_tag = self.python_version_tag
        self.logger.info(
            f"Targeting {app.python_source.title()} Python{app.python_version_tag}"
        )


class LinuxDebMostlyPassiveMixin(LinuxDebPassiveMixin):
    # The Mostly Passive mixin verifies that Docker exists and can be run, but
    # doesn't require that we're actually in a Linux environment.

    def docker_image_tag(self, app):
        """The Docker image tag for an app."""
        return (
            f"briefcase/{app.bundle}.{app.app_name.lower()}"
            f":{app.target_vendor}-{app.target_codename}-{self.python_source_tag(app)}"
        )

    def verify_tools(self):
        """If we're using Docker, verify that it is available."""
        super().verify_tools()
        if self.use_docker:
            Docker.verify(tools=self.tools)

    def verify_python(self, app):
        """Verify that the version of Python being used by the app is
        compatible with the version being used to run this.

        Will raise an exception if the Python version is fundamentally
        incompatible (i.e., if Briefcase doesn't support it); any other version
        discrepancy will log a warning, but continue.

        There's no need to invoke this unless you're using Docker. However,
        it won't *fail* in a no-docker config; it's just nonsensical to call.

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
        target_python_version = tuple(int(v) for v in target_python_tag.split("."))

        if target_python_version < (3, 8):
            raise BriefcaseCommandError(
                f"The system python3 version provided by {app.target_image} "
                f"is {target_python_tag}; Briefcase requires a "
                "minimum Python3 version of 3.8."
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

    Alternatively, you can change your `python_source` definition in
    `pyproject.toml` to `deadsnakes` to ensure that the Python used by
    the app at runtime is the same as your current Python environment.
    See the deb backend documentation for details:

    https://briefcase.readthedocs.io/en/stable/reference/platforms/linux/deb.html#python_source

*************************************************************************
"""
            )

    def verify_app_tools(self, app: AppConfig):
        """Verify App environment is prepared and available.

        When Docker is used, create or update a Docker image for the App.
        Without Docker, the host machine will be used as the App environment.

        :param app: The application being built
        """
        if self.use_docker:
            # Verifying the DockerAppContext is idempotent; but we have some
            # additional logic that we only want to run the first time through.
            # Check (and store) the pre-verify app tool state.
            verify_python = not hasattr(self.tools[app], "app_context")

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

        # Establish Docker as app context before letting super set subprocess
        super().verify_app_tools(app)


class LinuxDebMixin(LinuxDebMostlyPassiveMixin):
    def verify_host(self):
        """If we're *not* using Docker, verify that we're actually on a Debian-based Linux."""
        super().verify_host()
        if not self.use_docker:
            if self.tools.host_os != "Linux":
                raise UnsupportedHostError(self.supported_host_os_reason)

            # Debian-based distributions all have an /etc/debian_version
            if not Path("/etc/debian_version").exists():
                raise BriefcaseCommandError(
                    "Cannot build .deb packages on a Linux distribution that isn't Debian-based."
                )


class LinuxDebCreateCommand(LinuxDebMixin, CreateCommand):
    description = "Create and populate a .deb project."

    def output_format_template_context(self, app: AppConfig):
        context = super().output_format_template_context(app)

        # The base template context includes the host Python version;
        # override that with an app-specific Python version, allowing
        # for the app to be built with the system Python.
        context["python_version"] = app.python_version_tag

        # Add the docker base image
        context["docker_base_image"] = app.target_image

        # Add runtime package dependencies. App config has been finalized,
        # so this will be the target-specific definition, if one exists.
        # libc6 is added because lintian complains without it, even though
        # its a dependency of the thing we *do* care about - python.
        context["system_runtime_requires"] = ", ".join(
            [
                f"libc6 (>={app.glibc_version})",
                f"python{app.python_version_tag}",
            ]
            + getattr(app, "system_runtime_requires", [])
        )

        # The long description *must* exist.
        if app.long_description is None:
            raise BriefcaseCommandError(
                "pyproject.toml does not define `long_description`. "
                "Debian packaging guidelines require a long description."
            )

        return context

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

    Debian packaging guidelines require that packages provide a
    copyright statement. A dummy LICENSE file ({license_file.relative_to(self.base_path)})
    has been created. You should ensure this file is complete and
    correct before continuing.

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

    Debian packaging guidelines require that packages provide a
    change log. A dummy CHANGELOG file ({changelog_file.relative_to(self.base_path)})
    has been created. You should ensure this file is complete and
    correct before continuing.

*************************************************************************
"""
                )


class LinuxDebUpdateCommand(LinuxDebCreateCommand, UpdateCommand):
    description = "Update an existing .deb project."


class LinuxDebOpenCommand(LinuxDebMostlyPassiveMixin, OpenCommand):
    description = "Open a shell in a Docker container for an existing .deb project."

    def _open_app(self, app: AppConfig):
        # If we're using Docker, open an interactive shell in the container
        if self.use_docker:
            self.tools[app].app_context.run(["/bin/bash"], interactive=True)
        else:
            super()._open_app(app)


class LinuxDebBuildCommand(LinuxDebMixin, BuildCommand):
    description = "Build a .deb project."

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
                    f"Error while building app {app.app_name}."
                ) from e

        # Make the folder for docs
        doc_folder = self.package_path(app) / "usr" / "share" / "doc" / app.app_name
        doc_folder.mkdir(parents=True, exist_ok=True)

        with self.input.wait_bar("Installing license..."):
            license_file = self.bundle_path(app) / "LICENSE"
            if license_file.exists():
                self.tools.shutil.copy(license_file, doc_folder / "copyright")
            else:
                raise BriefcaseCommandError("LICENSE file is missing")

        with self.input.wait_bar("Installing changelog..."):
            changelog = self.bundle_path(app) / "CHANGELOG"
            if changelog.exists():
                with changelog.open() as infile:
                    outfile = gzip.GzipFile(
                        doc_folder / "changelog.gz", mode="w", mtime=0
                    )
                    outfile.write(infile.read().encode())
                    outfile.close()
            else:
                raise BriefcaseCommandError("CHANGELOG file is missing")

        # Make a folder for manpages
        man_folder = self.package_path(app) / "usr" / "share" / "man" / "man1"
        man_folder.mkdir(parents=True, exist_ok=True)

        with self.input.wait_bar("Installing man page..."):
            manpage_source = self.bundle_path(app) / f"{app.app_name}.1"
            if manpage_source.exists():
                with manpage_source.open() as infile:
                    outfile = gzip.GzipFile(
                        man_folder / f"{app.app_name}.1.gz", mode="w", mtime=0
                    )
                    outfile.write(infile.read().encode())
                    outfile.close()
            else:
                raise BriefcaseCommandError(
                    f"manpage source file `{manpage_source.relative_to(self.base_path)}` is missing"
                )

        self.logger.info("Update file permissions...")
        with self.input.wait_bar("Updating file permissions..."):
            for path in self.package_path(app).glob("**/*"):
                # File permissions like 775 and 664 (where the group and user
                # permissions are the same), cause Debian heartburn. So, if the
                # user and group permissions are the same, change the group
                # permission to the world permission.
                perms = os.stat(path).st_mode & 0o777
                user_perms = perms & 0o700
                group_perms = perms & 0o070
                if user_perms == (group_perms << 3):
                    world_perms = perms & 0o007
                    new_perms = user_perms | (world_perms << 3) | world_perms
                    self.logger.info(
                        "Updating file permissions on "
                        f"{path.relative_to(self.package_path(app))} "
                        f"from {oct(perms)[2:]} to {oct(new_perms)[2:]}"
                    )
                    path.chmod(new_perms)

        self.logger.info("Strip binary artefacts...")
        with self.input.wait_bar("Stripping binary artefacts..."):
            for path in itertools.chain(
                self.package_path(app).glob("**/*.so"),
                self.package_path(app).glob("**/*.so.1.0"),
                [self.binary_path(app)],
            ):
                self.logger.info(
                    f"Stripping {path.relative_to(self.package_path(app))}"
                )
                self.tools.subprocess.check_output(["strip", path])


class LinuxDebRunCommand(LinuxDebPassiveMixin, RunCommand):
    description = "Run a .deb project."
    supported_host_os = {"Linux"}
    supported_host_os_reason = "Linux .deb projects can only be executed on Linux."

    def run_app(self, app: AppConfig, test_mode: bool, **kwargs):
        """Start the application.

        :param app: The config object for the app
        :param test_mode: Boolean; Is the app running in test mode?
        """
        # Set up the log stream
        kwargs = self._prepare_app_env(app=app, test_mode=test_mode)

        # Start the app in a way that lets us stream the logs
        app_popen = self.tools.subprocess.Popen(
            [os.fsdecode(self.binary_path(app))],
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


class LinuxDebPackageCommand(LinuxDebMixin, PackageCommand):
    description = "Package a .deb project."

    def verify_tools(self):
        super().verify_tools()
        if not self.use_docker:
            if not Path("/usr/bin/dpkg-deb").exists():
                raise BriefcaseCommandError(
                    "Can't find the dpkg tools. Try running `sudo apt install dpkg-dev`."
                )

    def package_app(self, app: AppConfig, **kwargs):
        self.logger.info("Building .deb package...", prefix=app.app_name)
        with self.input.wait_bar("Building..."):
            try:
                # Build the bootstrap binary.
                self.tools[app].app_context.run(
                    [
                        "dpkg-deb",
                        "--build",
                        "--root-owner-group",
                        self.package_name(app),
                    ],
                    check=True,
                    cwd=self.bundle_path(app),
                )

                # Move the deb file to it's final location
                self.tools.shutil.move(
                    f"{self.bundle_path(app) / self.package_name(app)}.deb",
                    self.distribution_path(app, packaging_format="deb"),
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Error while building app {app.app_name}."
                ) from e


class LinuxDebPublishCommand(LinuxDebMixin, PublishCommand):
    description = "Publish a .deb project."


# Declare the briefcase command bindings
create = LinuxDebCreateCommand  # noqa
update = LinuxDebUpdateCommand  # noqa
open = LinuxDebOpenCommand  # noqa
build = LinuxDebBuildCommand  # noqa
run = LinuxDebRunCommand  # noqa
package = LinuxDebPackageCommand  # noqa
publish = LinuxDebPublishCommand  # noqa
