import os
import subprocess
from contextlib import contextmanager

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
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


class LinuxAppImageMixin(LinuxMixin):
    output_format = "appimage"

    def appdir_path(self, app):
        return self.bundle_path(app) / f"{app.formal_name}.AppDir"

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
    def run_in_build_environment(self, app):
        """Manager to execute OS commands in the build environment.

        Docker:
        Provides a context manager for the Docker context based on the
        properties of the app. This will replace self.subprocess with
        a version that proxies all subprocess calls into a docker container.

        Native:
        If the user has selected --no-docker, this is a no-op and commands
        are run in the native environment.

        :param app: The application that will determine the container image.
        """
        if self.use_docker:
            self.logger.info("Entering Docker context...", prefix=app.app_name)
            orig_subprocess = self.subprocess
            self.subprocess = self.Docker(self, app)
            self.subprocess.prepare()

            yield

            self.subprocess = orig_subprocess
            self.logger.info("Leaving Docker context", prefix=app.app_name)
        else:
            yield


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

        For Docker, using the container ensures that the right binary
        versions are installed.
        """
        with self.run_in_build_environment(app=app):
            super().install_app_dependencies(app=app)


class LinuxAppImageUpdateCommand(LinuxAppImageMixin, UpdateCommand):
    description = "Update an existing Linux AppImage."


class LinuxAppImageBuildCommand(LinuxAppImageMixin, BuildCommand):
    description = "Build a Linux AppImage."

    def verify_tools(self):
        """Verify that the AppImage linuxdeploy tool and plugins exist."""
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
            # However, if we are running inside Docker, we need to know the
            # environment *inside* the Docker container.
            with self.run_in_build_environment(app=app):
                echo_cmd = ["/bin/sh", "-c", "echo $PATH"]
                base_path = self.subprocess.check_output(echo_cmd).strip()

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

                # Build the app image. We use `--appimage-extract-and-run`
                # because AppImages won't run natively inside Docker.
                with self.run_in_build_environment(app=app):
                    self.subprocess.run(
                        [
                            self.linuxdeploy.file_path / self.linuxdeploy.file_name,
                            "--appimage-extract-and-run",
                            f"--appdir={self.appdir_path(app)}",
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


class LinuxAppImageRunCommand(LinuxAppImageMixin, RunCommand):
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
                [os.fsdecode(self.binary_path(app))],
                check=True,
                cwd=self.home_path,
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
build = LinuxAppImageBuildCommand  # noqa
run = LinuxAppImageRunCommand  # noqa
package = LinuxAppImagePackageCommand  # noqa
publish = LinuxAppImagePublishCommand  # noqa
