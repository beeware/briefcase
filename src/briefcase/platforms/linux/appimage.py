import os
import subprocess
from contextlib import contextmanager

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    OpenCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import verify_docker
from briefcase.integrations.linuxdeploy import LinuxDeploy
from briefcase.platforms.linux import LinuxMixin


class LinuxAppImagePassiveMixin(LinuxMixin):
    # The Passive mixin honors the docker options, but doesn't try to verify
    # docker exists. It is used by commands that are "passive" from the
    # perspective of the build system, like open and run.
    output_format = "appimage"

    def appdir_path(self, app):
        return self.bundle_path(app) / f"{app.formal_name}.AppDir"

    def project_path(self, app):
        return self.bundle_path(app)

    def binary_path(self, app):
        binary_name = app.formal_name.replace(" ", "_")
        return (
            self.platform_path
            / f"{binary_name}-{app.version}-{self.host_arch}.AppImage"
        )

    def distribution_path(self, app, packaging_format):
        return self.binary_path(app)

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "--no-docker",
            dest="use_docker",
            action="store_false",
            help="Don't use Docker for building the AppImage",
            required=False,
        )

    def parse_options(self, extra):
        """Extract the use_docker option."""
        options = super().parse_options(extra)

        self.use_docker = options.pop("use_docker")

        return options

    def clone_options(self, command):
        """Clone the use_docker option."""
        super().clone_options(command)
        self.use_docker = command.use_docker


class LinuxAppImageMixin(LinuxAppImagePassiveMixin):
    def docker_image_tag(self, app):
        """The Docker image tag for an app."""
        return (
            f"briefcase/{app.bundle}.{app.app_name.lower()}:py{self.python_version_tag}"
        )

    def verify_tools(self):
        """Verify that Docker is available; and if it isn't that we're on
        Linux."""
        super().verify_tools()
        if self.use_docker:
            if self.host_os == "Windows":
                raise BriefcaseCommandError(
                    "Linux AppImages cannot be generated on Windows."
                )
            else:
                self.Docker = verify_docker(self)
        elif self.host_os == "Linux":
            # Use subprocess natively. No Docker wrapper is needed
            self.Docker = None
        else:
            raise BriefcaseCommandError(
                "Linux AppImages can only be generated on Linux."
            )

    @contextmanager
    def dockerize(self, app):
        """Enter a Docker container based on the properties of the app.

        Provides a context manager for the Docker context. The context
        object is an object that exposes subprocess-analog calls.

        This will replace self.subprocess with a version that proxies all
        subprocess calls into the docker container.

        If the user has selected --no-docker, this is a no-op.

        :param app: The application that will determine the container image.
        """
        if self.use_docker:
            # Enter the Docker context.
            self.logger.info("Entering Docker context...", prefix=app.app_name)
            orig_subprocess = self.subprocess
            self.subprocess = self.Docker(self, app)

            yield self.subprocess

            self.logger.info("Leaving Docker context", prefix=app.app_name)
            self.subprocess = orig_subprocess
        else:
            yield self.subprocess


class LinuxAppImageCreateCommand(LinuxAppImageMixin, CreateCommand):
    description = "Create and populate a Linux AppImage."

    @property
    def support_package_url_query(self):
        """The query arguments to use in a support package query request."""
        return [
            ("platform", self.platform),
            ("version", self.python_version_tag),
            ("arch", self.host_arch),
        ]

    def install_app_dependencies(self, app: AppConfig):
        """Install application dependencies.

        This will be containerized in Docker to ensure that the right
        binary versions are installed.
        """
        with self.dockerize(app=app) as docker:
            docker.prepare()

            # Install dependencies. This will run inside a Docker container.
            super().install_app_dependencies(app=app)


class LinuxAppImageUpdateCommand(LinuxAppImageCreateCommand, UpdateCommand):
    description = "Update an existing Linux AppImage."


class LinuxAppImageOpenCommand(LinuxAppImagePassiveMixin, OpenCommand):
    description = "Open the folder containing an existing Linux AppImage project."


class LinuxAppImageBuildCommand(LinuxAppImageMixin, BuildCommand):
    description = "Build a Linux AppImage."

    def verify_tools(self):
        """Verify that the AppImage linuxdeploy tool and plugins exist.

        :param app: The application to build
        """
        super().verify_tools()
        self.linuxdeploy = LinuxDeploy.verify(self)

    def build_app(self, app: AppConfig, **kwargs):
        """Build an application.

        :param app: The application to build
        """
        # Build a dictionary of environment definitions that are required
        env = {}

        self.logger.info("Checking for Linuxdeploy plugins...", prefix=app.app_name)
        try:
            plugins = self.linuxdeploy.verify_plugins(
                app.linuxdeploy_plugins,
                bundle_path=self.bundle_path(app),
            )

            self.logger.info("Configuring Linuxdeploy plugins...", prefix=app.app_name)
            # We need to add the location of the linuxdeploy plugins to the PATH.
            # However, if we arerunning inside Docker, we need to know the
            # environment *inside* the Docker container.
            if self.use_docker:
                echo_cmd = ["/bin/bash", "-c", "echo $PATH"]
                base_path = self.Docker(self, app).check_output(echo_cmd).strip()
            else:
                base_path = self.os.environ["PATH"]

            # Add any plugin-required environment variables
            for plugin in plugins.values():
                env.update(plugin.env)

            # Construct a path that has been prepended with the path to the plugins
            env["PATH"] = os.pathsep.join(
                [os.fsdecode(plugin.file_path) for plugin in plugins.values()]
                + [base_path]
            )
        except AttributeError:
            self.logger.info("No linuxdeploy plugins configured.")
            plugins = {}

        self.logger.info("Building AppImage...", prefix=app.app_name)
        with self.input.wait_bar("Building..."):
            try:
                # For some reason, the version has to be passed in as an
                # environment variable, *not* in the configuration.
                env["VERSION"] = app.version
                # The internals of the binary aren't inherently visible, so
                # there's no need to package copyright files. These files
                # appear to be missing by default in the OS dev packages anyway,
                # so this effectively silences a bunch of warnings that can't
                # be easily resolved by the end user.
                env["DISABLE_COPYRIGHT_FILES_DEPLOYMENT"] = "1"
                # AppImages do not run natively within a Docker container. This
                # treats the AppImage like a self-extracting executable. Using
                # this environment variable instead of --appimage-extract-and-run
                # is necessary to ensure AppImage plugins are extracted as well.
                env["APPIMAGE_EXTRACT_AND_RUN"] = "1"
                # Explicitly declare target architecture as the current architecture.
                # This can be used by some linuxdeploy plugins.
                env["ARCH"] = self.host_arch

                # Find all the .so files in app and app_packages,
                # so they can be passed in to linuxdeploy to have their
                # dependencies added to the AppImage. Looks for any .so file
                # in the application, and make sure it is marked for deployment.
                so_folders = {
                    so_file.parent for so_file in self.appdir_path(app).glob("**/*.so")
                }

                additional_args = []
                for folder in sorted(so_folders):
                    additional_args.extend(["--deploy-deps-only", str(folder)])

                for plugin in plugins:
                    additional_args.extend(["--plugin", plugin])

                # Build the AppImage.
                with self.dockerize(app) as docker:
                    docker.run(
                        [
                            self.linuxdeploy.file_path / self.linuxdeploy.file_name,
                            "--appdir",
                            os.fsdecode(self.appdir_path(app)),
                            "--desktop-file",
                            os.fsdecode(
                                self.appdir_path(app)
                                / f"{app.bundle}.{app.app_name}.desktop"
                            ),
                            "--output",
                            "appimage",
                        ]
                        + additional_args,
                        env=env,
                        check=True,
                        cwd=self.platform_path,
                    )

                # Make the binary executable.
                self.os.chmod(self.binary_path(app), 0o755)
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Error while building app {app.app_name}."
                ) from e


class LinuxAppImageRunCommand(LinuxAppImagePassiveMixin, RunCommand):
    description = "Run a Linux AppImage."

    def verify_tools(self):
        """Verify that we're on Linux."""
        super().verify_tools()
        if self.host_os != "Linux":
            raise BriefcaseCommandError("AppImages can only be executed on Linux.")

    def run_app(self, app: AppConfig, **kwargs):
        """Start the application.

        :param app: The config object for the app
        """
        self.logger.info("Starting app...", prefix=app.app_name)
        try:
            self.subprocess.run(
                [
                    os.fsdecode(self.binary_path(app)),
                ],
                check=True,
                cwd=self.home_path,
                stream_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Unable to start app {app.app_name}.") from e


class LinuxAppImagePackageCommand(LinuxAppImageMixin, PackageCommand):
    description = "Package a Linux AppImage."


class LinuxAppImagePublishCommand(LinuxAppImageMixin, PublishCommand):
    description = "Publish a Linux AppImage."


# Declare the briefcase command bindings
create = LinuxAppImageCreateCommand  # noqa
update = LinuxAppImageUpdateCommand  # noqa
open = LinuxAppImageOpenCommand  # noqa
build = LinuxAppImageBuildCommand  # noqa
run = LinuxAppImageRunCommand  # noqa
package = LinuxAppImagePackageCommand  # noqa
publish = LinuxAppImagePublishCommand  # noqa
