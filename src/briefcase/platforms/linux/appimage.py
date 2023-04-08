import os
import subprocess
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
from briefcase.exceptions import (
    BriefcaseCommandError,
    BriefcaseConfigError,
    UnsupportedHostError,
)
from briefcase.integrations.docker import Docker, DockerAppContext
from briefcase.integrations.linuxdeploy import LinuxDeploy
from briefcase.integrations.subprocess import NativeAppContext
from briefcase.platforms.linux import (
    DockerOpenCommand,
    LinuxMixin,
    LocalRequirementsMixin,
)


class LinuxAppImagePassiveMixin(LinuxMixin):
    # The Passive mixin honors the docker options, but doesn't try to verify
    # docker exists. It is used by commands that are "passive" from the
    # perspective of the build system, like open and run.
    output_format = "appimage"
    supported_host_os = {"Darwin", "Linux"}
    supported_host_os_reason = (
        "Linux AppImages can only be built on Linux, or on macOS using Docker."
    )

    def appdir_path(self, app):
        return self.bundle_path(app) / f"{app.formal_name}.AppDir"

    def project_path(self, app):
        return self.bundle_path(app)

    def binary_name(self, app):
        safe_name = app.formal_name.replace(" ", "_")
        return f"{safe_name}-{app.version}-{self.tools.host_arch}.AppImage"

    def binary_path(self, app):
        return self.bundle_path(app) / self.binary_name(app)

    def distribution_path(self, app):
        return self.dist_path / self.binary_name(app)

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

    def finalize_app_config(self, app: AppConfig):
        """If we're *not* using Docker, warn the user about portability."""
        if not self.use_docker:
            self.logger.warning(
                """\
*************************************************************************
** WARNING: Building a Local AppImage!                                 **
*************************************************************************

    You are building an AppImage outside Docker. The resulting AppImage
    will work, but will not be as portable as a Docker-based AppImage.
    Any `manylinux` setting will be ignored.

*************************************************************************
"""
            )


class LinuxAppImageMostlyPassiveMixin(LinuxAppImagePassiveMixin):
    # The Mostly Passive mixin verifies that Docker exists and can be run, but
    # doesn't require that we're actually in a Linux environment.
    def docker_image_tag(self, app):
        """The Docker image tag for an app."""
        try:
            return f"briefcase/{app.bundle}.{app.app_name.lower()}:{app.manylinux}-appimage"
        except AttributeError:
            return f"briefcase/{app.bundle}.{app.app_name.lower()}:appimage"

    def verify_tools(self):
        """If we're using docker, verify that it is available."""
        super().verify_tools()
        if self.use_docker:
            Docker.verify(tools=self.tools)

    def verify_app_tools(self, app: AppConfig):
        """Verify App environment is prepared and available.

        When Docker is used, create or update a Docker image for the App.
        Without Docker, the host machine will be used as the App environment.

        :param app: The application being built
        """
        if self.use_docker:
            DockerAppContext.verify(
                tools=self.tools,
                app=app,
                image_tag=self.docker_image_tag(app),
                dockerfile_path=self.bundle_path(app) / "Dockerfile",
                app_base_path=self.base_path,
                host_bundle_path=self.bundle_path(app),
                host_data_path=self.data_path,
                python_version=self.python_version_tag,
            )
        else:
            NativeAppContext.verify(tools=self.tools, app=app)

        # Establish Docker as app context before letting super set subprocess
        super().verify_app_tools(app)


class LinuxAppImageMixin(LinuxAppImageMostlyPassiveMixin):
    def verify_host(self):
        """If we're *not* using Docker, verify that we're actually on Linux."""
        super().verify_host()
        if not self.use_docker and self.tools.host_os != "Linux":
            raise UnsupportedHostError(self.supported_host_os_reason)


class LinuxAppImageCreateCommand(
    LinuxAppImageMixin,
    LocalRequirementsMixin,
    CreateCommand,
):
    description = "Create and populate a Linux AppImage."

    def output_format_template_context(self, app: AppConfig):
        context = super().output_format_template_context(app)
        # Add the manylinux tag to the template context.
        try:
            tag = getattr(app, "manylinux_image_tag", "latest")
            context["manylinux_image"] = f"{app.manylinux}_{self.tools.host_arch}:{tag}"
            if app.manylinux in {"manylinux1", "manylinux2010", "manylinux2014"}:
                context["vendor_base"] = "centos"
            elif app.manylinux == "manylinux_2_24":
                context["vendor_base"] = "debian"
            elif app.manylinux.startswith("manylinux_2_"):
                context["vendor_base"] = "almalinux"
            else:
                raise BriefcaseConfigError(
                    f"""Unknown manylinux tag {app.manylinux!r}"""
                )
        except AttributeError:
            pass

        return context


class LinuxAppImageUpdateCommand(LinuxAppImageCreateCommand, UpdateCommand):
    description = "Update an existing Linux AppImage."


class LinuxAppImageOpenCommand(LinuxAppImageMostlyPassiveMixin, DockerOpenCommand):
    description = (
        "Open a shell in a Docker container for an existing Linux AppImage project."
    )


class LinuxAppImageBuildCommand(LinuxAppImageMixin, BuildCommand):
    description = "Build a Linux AppImage."

    def verify_tools(self):
        """Verify the AppImage linuxdeploy tool and plugins exist."""
        super().verify_tools()
        LinuxDeploy.verify(tools=self.tools)

    def build_app(self, app: AppConfig, **kwargs):
        """Build an application.

        :param app: The application to build
        """
        # Build a dictionary of environment definitions that are required
        env = {}

        self.logger.info("Checking for Linuxdeploy plugins...", prefix=app.app_name)
        try:
            plugins = self.tools.linuxdeploy.verify_plugins(
                app.linuxdeploy_plugins,
                bundle_path=self.bundle_path(app),
            )

            self.logger.info("Configuring Linuxdeploy plugins...", prefix=app.app_name)
            # We need to add the location of the linuxdeploy plugins to the PATH.
            # However, if we are running inside Docker, we need to know the
            # environment *inside* the Docker container.
            echo_cmd = ["/bin/sh", "-c", "echo $PATH"]
            base_path = self.tools[app].app_context.check_output(echo_cmd).strip()

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
                env["ARCH"] = self.tools.host_arch

                # Find all the .so files in app and app_packages,
                # so they can be passed in to linuxdeploy to have their
                # requirements added to the AppImage. Looks for any .so file
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
                self.tools[app].app_context.run(
                    [
                        self.tools.linuxdeploy.file_path
                        / self.tools.linuxdeploy.file_name,
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
                    cwd=self.bundle_path(app),
                )

                # Make the binary executable.
                self.tools.os.chmod(self.binary_path(app), 0o755)
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Error while building app {app.app_name}."
                ) from e


class LinuxAppImageRunCommand(LinuxAppImagePassiveMixin, RunCommand):
    description = "Run a Linux AppImage."
    supported_host_os = {"Linux"}
    supported_host_os_reason = "Linux AppImages can only be executed on Linux."

    def run_app(
        self,
        app: AppConfig,
        test_mode: bool,
        passthrough: List[str],
        **kwargs,
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


class LinuxAppImagePackageCommand(LinuxAppImageMixin, PackageCommand):
    description = "Package a Linux AppImage."

    def package_app(self, app: AppConfig, **kwargs):
        """Package an AppImage.

        :param app: The application to package
        """
        self.tools.shutil.copy(self.binary_path(app), self.distribution_path(app))


class LinuxAppImagePublishCommand(LinuxAppImageMixin, PublishCommand):
    description = "Publish a Linux AppImage."


# Declare the briefcase command bindings
create = LinuxAppImageCreateCommand
update = LinuxAppImageUpdateCommand
open = LinuxAppImageOpenCommand
build = LinuxAppImageBuildCommand
run = LinuxAppImageRunCommand
package = LinuxAppImagePackageCommand
publish = LinuxAppImagePublishCommand
