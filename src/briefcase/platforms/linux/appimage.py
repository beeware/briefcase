import os
import subprocess
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
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.docker import Docker, DockerAppContext
from briefcase.integrations.linuxdeploy import LinuxDeploy
from briefcase.integrations.subprocess import NativeAppContext
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
            / f"{binary_name}-{app.version}-{self.tools.host_arch}.AppImage"
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


class LinuxAppImageMostlyPassiveMixin(LinuxAppImagePassiveMixin):
    def docker_image_tag(self, app):
        """The Docker image tag for an app."""
        return (
            f"briefcase/{app.bundle}.{app.app_name.lower()}:py{self.python_version_tag}"
        )

    def verify_tools(self):
        """If we're using docker, verify that it is available."""
        super().verify_tools()
        if self.use_docker:
            if self.tools.host_os == "Windows":
                raise BriefcaseCommandError(
                    "Linux AppImages cannot be generated on Windows."
                )
            else:
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
                host_platform_path=self.platform_path,
                host_data_path=self.data_path,
                python_version=self.python_version_tag,
            )
        else:
            NativeAppContext.verify(tools=self.tools, app=app)

        # Establish Docker as app context before letting super set subprocess
        super().verify_app_tools(app)

    def _requirements_mounts(self, app: AppConfig):
        """Generate the list of Docker volume mounts needed to support local
        requirements.

        This list of mounts will include *all* possible requirements (i.e.,
        `requires` *and* `test_requires`)

        :param app: The app for which requirement mounts are needed
        :returns: A list of (source, target) pairs; source is a fully resolved
            local filesystem path; target is a path on the Docker filesystem.
        """
        requires = app.requires.copy() if app.requires else []
        if app.test_requires:
            requires.extend(app.test_requires)

        mounts = []
        for requirement in requires:
            if _is_local_requirement(requirement):
                source = Path(requirement).resolve()
                mounts.append((str(source), f"/requirements/{source.name}"))

        return mounts


class LinuxAppImageMixin(LinuxAppImageMostlyPassiveMixin):
    def verify_tools(self):
        """If we're *not* using Docker, verify that we're actually on Linux."""
        super().verify_tools()
        if not self.use_docker and self.tools.host_os != "Linux":
            raise BriefcaseCommandError(
                "Linux AppImages can only be generated on Linux without Docker."
            )


class LinuxAppImageCreateCommand(LinuxAppImageMixin, CreateCommand):
    description = "Create and populate a Linux AppImage."

    def support_package_filename(self, support_revision):
        """The query arguments to use in a support package query request."""
        return f"Python-{self.python_version_tag}-linux-{self.tools.host_arch}-support.b{support_revision}.tar.gz"

    def support_package_url(self, support_revision):
        """The URL of the support package to use for apps of this type."""
        return (
            "https://briefcase-support.s3.amazonaws.com/"
            f"python/{self.python_version_tag}/{self.platform}/{self.tools.host_arch}/"
            + self.support_package_filename(support_revision)
        )

    def _pip_requires(self, requires: List[str]):
        """Convert the requirements list to an AppImage compatible format.

        If running in no-docker mode, this returns the requirements as specified
        by the user.

        If running in Docker mode, any local file requirements are converted into
        a reference in the /requirements mount folder.

        :param requires: The user-specified list of app requirements
        :returns: The final list of requirement arguments to pass to pip
        """
        original = super()._pip_requires(requires)
        if not self.use_docker:
            return original

        final = []
        for requirement in original:
            if _is_local_requirement(requirement):
                source = Path(requirement).resolve()
                final.append(f"/requirements/{source.name}")
            else:
                # Use the requirement as-specified
                final.append(requirement)

        return final

    def _pip_kwargs(self, app: AppConfig):
        """Generate the kwargs to pass when invoking pip.

        Adds any mounts needed to support local file requirements.

        :param app: The app configuration
        :returns: The kwargs to pass to the pip call
        """
        kwargs = super()._pip_kwargs(app)

        if self.use_docker:
            mounts = self._requirements_mounts(app)
            if mounts:
                kwargs["mounts"] = mounts

        return kwargs


class LinuxAppImageUpdateCommand(LinuxAppImageCreateCommand, UpdateCommand):
    description = "Update an existing Linux AppImage."


class LinuxAppImageOpenCommand(LinuxAppImageMostlyPassiveMixin, OpenCommand):
    description = "Open the folder containing an existing Linux AppImage project."

    def _open_app(self, app: AppConfig):
        # If we're using Docker, open an interactive shell in the container
        if self.use_docker:
            kwargs = {}
            mounts = self._requirements_mounts(app)
            if mounts:
                kwargs["mounts"] = mounts

            self.tools[app].app_context.run(
                ["/bin/bash"],
                interactive=True,
                **kwargs,
            )
        else:
            super()._open_app(app)


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
                    cwd=self.platform_path,
                )

                # Make the binary executable.
                self.tools.os.chmod(self.binary_path(app), 0o755)
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Error while building app {app.app_name}."
                ) from e


class LinuxAppImageRunCommand(LinuxAppImagePassiveMixin, RunCommand):
    description = "Run a Linux AppImage."

    def verify_tools(self):
        """Verify that we're on Linux."""
        super().verify_tools()
        if self.tools.host_os != "Linux":
            raise BriefcaseCommandError("AppImages can only be executed on Linux.")

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
