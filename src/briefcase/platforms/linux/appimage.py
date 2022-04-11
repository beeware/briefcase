import os
import subprocess
from contextlib import contextmanager

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand
)
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import verify_docker
from briefcase.integrations.linuxdeploy import LinuxDeploy
from briefcase.platforms.linux import LinuxMixin


class LinuxAppImageMixin(LinuxMixin):
    output_format = 'appimage'

    def appdir_path(self, app):
        return self.bundle_path(app) / "{app.formal_name}.AppDir".format(app=app)

    def binary_path(self, app):
        binary_name = app.formal_name.replace(' ', '_')
        return self.platform_path / '{binary_name}-{app.version}-{self.host_arch}.AppImage'.format(
            app=app,
            self=self,
            binary_name=binary_name,
        )

    def distribution_path(self, app, packaging_format):
        return self.binary_path(app)

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            '--no-docker',
            dest='use_docker',
            action='store_false',
            help="Don't use Docker for building the AppImage",
            required=False,
        )

    def parse_options(self, extra):
        """Extract the use_docker option"""
        options = super().parse_options(extra)

        self.use_docker = options.pop('use_docker')

        return options

    def clone_options(self, command):
        """Clone the use_docker option"""
        super().clone_options(command)
        self.use_docker = command.use_docker

    def docker_image_tag(self, app):
        "The Docker image tag for an app"
        return 'briefcase/{app.bundle}.{app_name}:py{self.python_version_tag}'.format(
            app=app,
            self=self,
            app_name=app.app_name.lower()
        )

    def verify_tools(self):
        """
        Verify that Docker is available; and if it isn't that we're on Linux.
        """
        super().verify_tools()
        if self.use_docker:
            if self.host_os == 'Windows':
                raise BriefcaseCommandError("""
Linux AppImages cannot be generated on Windows.
""")
            else:
                self.Docker = verify_docker(self)
        else:
            if self.host_os == 'Linux':
                # Use subprocess natively. No Docker wrapper is needed
                self.Docker = None
            else:
                raise BriefcaseCommandError("""
Linux AppImages can only be generated on Linux.
""")

    @contextmanager
    def dockerize(self, app):
        """
        Enter a Docker container based on the properties of the app.

        Provides a context manager for the Docker context. The context
        object is an object that exposes subprocess-analog calls.

        This will replace self.subprocess with a version that proxies all
        subprocess calls into the docker container.

        If the user has selected --no-docker, this is a no-op.

        :param app: The application that will determine the container image.
        """
        if self.use_docker:
            """
            Enter the Docker context.
            """
            print("[{app.app_name}] Entering Docker context...".format(app=app))
            orig_subprocess = self.subprocess
            self.subprocess = self.Docker(self, app)

            yield self.subprocess

            print("[{app.app_name}] Leaving Docker context.".format(app=app))
            self.subprocess = orig_subprocess
        else:
            yield self.subprocess


class LinuxAppImageCreateCommand(LinuxAppImageMixin, CreateCommand):
    description = "Create and populate a Linux AppImage."

    @property
    def support_package_url_query(self):
        """
        The query arguments to use in a support package query request.
        """
        return [
            ('platform', self.platform),
            ('version', self.python_version_tag),
            ('arch', self.host_arch),
        ]

    def install_app_dependencies(self, app: BaseConfig):
        """
        Install application dependencies.

        This will be containerized in Docker to ensure that the right
        binary versions are installed.
        """
        with self.dockerize(app=app) as docker:
            docker.prepare()

            # Install dependencies. This will run inside a Docker container.
            super().install_app_dependencies(app=app)


class LinuxAppImageUpdateCommand(LinuxAppImageMixin, UpdateCommand):
    description = "Update an existing Linux AppImage."


class LinuxAppImageBuildCommand(LinuxAppImageMixin, BuildCommand):
    description = "Build a Linux AppImage."

    def verify_tools(self):
        super().verify_tools()
        self.linuxdeploy = LinuxDeploy.verify(self)

    def build_app(self, app: BaseConfig, **kwargs):
        """
        Build an application.

        :param app: The application to build
        """
        print()
        print("[{app.app_name}] Building AppImage...".format(app=app))

        try:
            print()
            # Build the AppImage.
            # For some reason, the version has to be passed in as an
            # environment variable, *not* in the configuration...
            env = {
                'VERSION': app.version
            }

            # Find all the .so files in app and app_packages,
            # so they can be passed in to linuxdeploy to have their
            # dependencies added to the AppImage. Looks for any .so file
            # in the application, and make sure it is marked for deployment.
            so_folders = set()
            for so_file in self.appdir_path(app).glob('**/*.so'):
                so_folders.add(so_file.parent)

            deploy_deps_args = []
            for folder in sorted(so_folders):
                deploy_deps_args.extend(["--deploy-deps-only", str(folder)])

            # Build the app image. We use `--appimage-extract-and-run`
            # because AppImages won't run natively inside Docker.
            with self.dockerize(app) as docker:
                docker.run(
                    [
                        self.linuxdeploy.appimage_path,
                        "--appimage-extract-and-run",
                        "--appdir={appdir_path}".format(appdir_path=self.appdir_path(app)),
                        "-d", os.fsdecode(
                            self.appdir_path(app) / "{app.bundle}.{app.app_name}.desktop".format(
                                app=app,
                            )
                        ),
                        "-o", "appimage",
                    ] + deploy_deps_args,
                    env=env,
                    check=True,
                    cwd=self.platform_path
                )

            # Make the binary executable.
            self.os.chmod(self.binary_path(app), 0o755)
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Error while building app {app.app_name}.".format(app=app)
            )


class LinuxAppImageRunCommand(LinuxAppImageMixin, RunCommand):
    description = "Run a Linux AppImage."

    def verify_tools(self):
        """
        Verify that we're on Linux.
        """
        super().verify_tools()
        if self.host_os != 'Linux':
            raise BriefcaseCommandError(
                "AppImages can only be executed on Linux."
            )

    def run_app(self, app: BaseConfig, **kwargs):
        """
        Start the application.

        :param app: The config object for the app
        :param base_path: The path to the project directory.
        """
        print()
        print('[{app.app_name}] Starting app...'.format(
            app=app
        ))
        try:
            print()
            self.subprocess.run(
                [
                    os.fsdecode(self.binary_path(app)),
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Unable to start app {app.app_name}.".format(app=app)
            )


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
