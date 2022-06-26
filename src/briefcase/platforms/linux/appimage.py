import os
import pathlib
import subprocess
import urllib
from contextlib import contextmanager

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import verify_docker
from briefcase.integrations.linuxdeploy import (
    LinuxDeploy,
    LinuxDeployGtkPlugin,
    LinuxDeployLocalPlugin,
    LinuxDeployUrlPlugin,
)
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

    def verify_tools(self, app: BaseConfig):
        """Verify that Docker is available; and if it isn't that we're on
        Linux."""
        super().verify_tools(app)
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

    def install_app_dependencies(self, app: BaseConfig):
        """Install application dependencies.

        This will be containerized in Docker to ensure that the right
        binary versions are installed.
        """
        with self.dockerize(app=app) as docker:
            docker.prepare()

            # Install dependencies. This will run inside a Docker container.
            super().install_app_dependencies(app=app)


class LinuxAppImageUpdateCommand(LinuxAppImageMixin, UpdateCommand):
    description = "Update an existing Linux AppImage."


def _valid_url(url: str) -> bool:
    """Check that a URL is valid.

    :param url: The URL to check.
    """
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


class LinuxAppImageBuildCommand(LinuxAppImageMixin, BuildCommand):
    description = "Build a Linux AppImage."

    def verify_tools(self, app: BaseConfig):
        """Verify that the AppImage linuxdeploy tool and plugins exist.

        :param app: The application to build
        """
        super().verify_tools(app)
        self.linuxdeploy = LinuxDeploy.verify(self)
        if app.linuxdeploy_plugins:
            for plugin in app.linuxdeploy_plugins:
                if " " in plugin:
                    _, plugin = plugin.split(" ")
                plugin_path = pathlib.Path(plugin)
                if plugin == "gtk":
                    LinuxDeployGtkPlugin.verify(self)
                elif _valid_url(plugin) or plugin_path.is_file():
                    LinuxDeployUrlPlugin.verify(self, plugin=plugin)
                elif plugin_path.is_file():
                    LinuxDeployLocalPlugin.verify(self, plugin=plugin)
                else:
                    self.logger.info(f"unable to verify plugin {plugin}")

    def build_app(self, app: BaseConfig, **kwargs):
        """Build an application.

        :param app: The application to build
        """
        self.logger.info("Building AppImage...", prefix=app.app_name)

        with self.input.wait_bar("Building..."):
            try:
                self._build_appimage(app)
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Error while building app {app.app_name}."
                ) from e

    def _build_appimage(self, app: BaseConfig):
        """Build the AppImage.

        :param app: The application to build
        """

        # For some reason, the version has to be passed in as an
        # environment variable, *not* in the configuration...
        env = {"VERSION": app.version}

        plugins = []
        if app.linuxdeploy_plugins:
            for plugin in app.linuxdeploy_plugins:
                env_var = None
                if " " in plugin:
                    env_var, plugin = plugin.split(" ")
                    var, value = env_var.split("=")
                    env[var] = value
                if plugin == "gtk":
                    plugins.append(plugin)
                    if not env_var:
                        env["DEPLOY_GTK_VERSION"] = "3"
                else:
                    filename_stem = pathlib.Path(plugin).stem
                    plugin_name = filename_stem.split("-")[-1]
                    plugins.append(plugin_name)

        else:
            self.logger.info("No linuxdeploy plugins configured")

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
        with self.dockerize(app) as docker:
            docker.run(
                [
                    self.linuxdeploy.file_path,
                    "--appimage-extract-and-run",
                    f"--appdir={self.appdir_path(app)}",
                    "-d",
                    os.fsdecode(
                        self.appdir_path(app) / f"{app.bundle}.{app.app_name}.desktop"
                    ),
                    "-o",
                    "appimage",
                ]
                + additional_args,
                env=env,
                check=True,
                cwd=self.platform_path,
            )

        # Make the binary executable.
        self.os.chmod(self.binary_path(app), 0o755)


class LinuxAppImageRunCommand(LinuxAppImageMixin, RunCommand):
    description = "Run a Linux AppImage."

    def verify_tools(self, app: BaseConfig):
        """Verify that we're on Linux."""
        super().verify_tools(app)
        if self.host_os != "Linux":
            raise BriefcaseCommandError("AppImages can only be executed on Linux.")

    def run_app(self, app: BaseConfig, **kwargs):
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
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(f"Unable to start app {app.app_name}.") from e


class LinuxAppImagePackageCommand(LinuxAppImageMixin, PackageCommand):
    description = "Publish a Linux AppImage."


class LinuxAppImagePublishCommand(LinuxAppImageMixin, PublishCommand):
    description = "Publish a Linux AppImage."


# Declare the briefcase command bindings
create = LinuxAppImageCreateCommand  # noqa
update = LinuxAppImageUpdateCommand  # noqa
build = LinuxAppImageBuildCommand  # noqa
run = LinuxAppImageRunCommand  # noqa
package = LinuxAppImagePackageCommand  # noqa
publish = LinuxAppImagePublishCommand  # noqa
