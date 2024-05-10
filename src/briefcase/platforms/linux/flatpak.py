from __future__ import annotations

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
from briefcase.exceptions import BriefcaseConfigError
from briefcase.integrations.flatpak import Flatpak
from briefcase.platforms.linux import LinuxMixin


class LinuxFlatpakMixin(LinuxMixin):
    output_format = "flatpak"
    supported_host_os = {"Linux"}
    supported_host_os_reason = "Flatpaks can only be built on Linux."

    def binary_path(self, app):
        # Flatpak doesn't really produce an identifiable "binary" as part of its
        # build process, so the SDK wrapper creates a file that can use to identify
        # if run has been invoked. As a neat side effect, it's also a shell script
        # that can invoke the flatpak.
        return self.bundle_path(app) / app.bundle_identifier

    def project_path(self, app):
        return self.bundle_path(app)

    def distribution_path(self, app):
        binary_name = app.formal_name.replace(" ", "_")
        return (
            self.dist_path
            / f"{binary_name}-{app.version}-{self.tools.host_arch}.flatpak"
        )

    def verify_tools(self):
        """Verify that we're on Linux."""
        super().verify_tools()
        Flatpak.verify(tools=self.tools)

    def flatpak_runtime_repo(self, app):
        try:
            repo_url = app.flatpak_runtime_repo_url
            try:
                repo_alias = app.flatpak_runtime_repo_alias
            except AttributeError:
                raise BriefcaseConfigError(
                    "If you specify a custom Flatpak runtime repository, "
                    "you must also specify an alias for that repository using "
                    "`flatpak_runtime_repo_alias`"
                )

        except AttributeError:
            repo_alias = Flatpak.DEFAULT_REPO_ALIAS
            repo_url = Flatpak.DEFAULT_REPO_URL

        return repo_alias, repo_url

    def flatpak_runtime(self, app):
        try:
            return app.flatpak_runtime
        except AttributeError as e:
            raise BriefcaseConfigError(
                """\
The App does not specify the Flatpak runtime to use.

Your application configuration must provide values for
`flatpak_sdk`, `flatpak_runtime`, and `flatpak_runtime_version`.
"""
            ) from e

    def flatpak_runtime_version(self, app):
        try:
            return app.flatpak_runtime_version
        except AttributeError as e:
            raise BriefcaseConfigError(
                """\
The App does not specify the version of the Flatpak runtime to use.

Your application configuration must provide values for
`flatpak_sdk`, `flatpak_runtime`, and `flatpak_runtime_version`.
"""
            ) from e

    def flatpak_sdk(self, app):
        try:
            return app.flatpak_sdk
        except AttributeError as e:
            raise BriefcaseConfigError(
                """\
The App does not specify the Flatpak SDK to use.

Your application configuration must provide values for
`flatpak_sdk`, `flatpak_runtime`, and `flatpak_runtime_version`.
"""
            ) from e


class LinuxFlatpakCreateCommand(LinuxFlatpakMixin, CreateCommand):
    description = "Create and populate a Linux Flatpak."
    hidden_app_properties = {"permission", "finish_arg"}

    def output_format_template_context(self, app: AppConfig):
        """Add flatpak runtime/SDK details to the app template."""
        return {
            "flatpak_runtime": self.flatpak_runtime(app),
            "flatpak_runtime_version": self.flatpak_runtime_version(app),
            "flatpak_sdk": self.flatpak_sdk(app),
        }

    def permissions_context(self, app: AppConfig, x_permissions: dict[str, str]):
        """Additional template context for permissions.

        :param app: The config object for the app
        :param x_permissions: The dictionary of known cross-platform permission
            definitions.
        :returns: The template context describing permissions for the app.
        """
        # The default finish arguments that Briefcase adds on every Flatpak.
        finish_args = {
            # X11 + XShm access
            "share=ipc": True,
            "socket=x11": True,
            # Disable Wayland access
            "nosocket=wayland": True,
            # Network access
            "share=network": True,
            # GPU access
            "device=dri": True,
            # Sound access
            "socket=pulseaudio": True,
            # Host filesystem access
            "filesystem=xdg-cache": True,
            "filesystem=xdg-config": True,
            "filesystem=xdg-data": True,
            "filesystem=xdg-documents": True,
            # DBus access
            "socket=session-bus": True,
        }

        finish_args.update(getattr(app, "finish_arg", {}))

        return {
            "finish_args": finish_args,
        }


class LinuxFlatpakUpdateCommand(LinuxFlatpakCreateCommand, UpdateCommand):
    description = "Update an existing Linux Flatpak."


class LinuxFlatpakOpenCommand(LinuxFlatpakMixin, OpenCommand):
    description = "Open the folder containing an existing Linux Flatpak project."


class LinuxFlatpakBuildCommand(LinuxFlatpakMixin, BuildCommand):
    description = "Build a Linux Flatpak."

    def build_app(self, app: AppConfig, **kwargs):
        """Build an application.

        :param app: The application to build
        """
        self.logger.info(
            "Ensuring Flatpak runtime for the app is available...",
            prefix=app.app_name,
        )
        flatpak_repo_alias, flatpak_repo_url = self.flatpak_runtime_repo(app)

        with self.input.wait_bar("Ensuring Flatpak runtime repo is registered..."):
            self.tools.flatpak.verify_repo(
                repo_alias=flatpak_repo_alias,
                url=flatpak_repo_url,
            )

        # ``flatpak install`` uses a lot of console animations, and there
        # doesn't appear to be a way to turn off these animations. Use those
        # native animations rather than wrapping in a wait_bar.
        self.tools.flatpak.verify_runtime(
            repo_alias=flatpak_repo_alias,
            runtime=self.flatpak_runtime(app),
            runtime_version=self.flatpak_runtime_version(app),
            sdk=self.flatpak_sdk(app),
        )

        self.logger.info("Building Flatpak...", prefix=app.app_name)
        with self.input.wait_bar("Building..."):
            self.tools.flatpak.build(
                bundle_identifier=app.bundle_identifier,
                app_name=app.app_name,
                path=self.bundle_path(app),
            )


class LinuxFlatpakRunCommand(LinuxFlatpakMixin, RunCommand):
    description = "Run a Linux Flatpak."

    def run_app(
        self,
        app: AppConfig,
        test_mode: bool,
        passthrough: list[str],
        **kwargs,
    ):
        """Start the application.

        :param app: The config object for the app
        :param test_mode: Boolean; Is the app running in test mode?
        :param passthrough: The list of arguments to pass to the app
        """
        # Set up the log stream
        kwargs = self._prepare_app_kwargs(app=app, test_mode=test_mode)

        # Starting a flatpak has slightly different startup arguments; however,
        # the rest of the app startup process is the same. Transform the output
        # of the "default" behavior to be in flatpak format.
        if test_mode:
            kwargs = {"main_module": kwargs["env"]["BRIEFCASE_MAIN_MODULE"]}
        else:
            kwargs = {}

        # Console apps must operate in non-streaming mode so that console input can
        # be handled correctly. However, if we're in test mode, we *must* stream so
        # that we can see the test exit sentinel
        if app.console_app and not test_mode:
            self.logger.info("=" * 75)
            self.tools.flatpak.run(
                bundle_identifier=app.bundle_identifier,
                args=passthrough,
                stream_output=False,
                **kwargs,
            )
        else:
            # Start the app in a way that lets us stream the logs
            app_popen = self.tools.flatpak.run(
                bundle_identifier=app.bundle_identifier,
                args=passthrough,
                stream_output=True,
                **kwargs,
            )

            # Start streaming logs for the app.
            self._stream_app_logs(
                app,
                popen=app_popen,
                test_mode=test_mode,
                clean_output=False,
            )


class LinuxFlatpakPackageCommand(LinuxFlatpakMixin, PackageCommand):
    description = "Package a Linux Flatpak for distribution."

    def package_app(self, app: AppConfig, **kwargs):
        """Start the application.

        :param app: The config object for the app
        """
        self.logger.info("Building bundle...", prefix=app.app_name)
        with self.input.wait_bar("Bundling..."):
            _, flatpak_repo_url = self.flatpak_runtime_repo(app)
            self.tools.flatpak.bundle(
                repo_url=flatpak_repo_url,
                bundle_identifier=app.bundle_identifier,
                app_name=app.app_name,
                version=app.version,
                build_path=self.bundle_path(app),
                output_path=self.distribution_path(app),
            )


class LinuxFlatpakPublishCommand(LinuxFlatpakMixin, PublishCommand):
    description = "Publish a Linux Flatpak."


# Declare the briefcase command bindings
create = LinuxFlatpakCreateCommand
update = LinuxFlatpakUpdateCommand
open = LinuxFlatpakOpenCommand
build = LinuxFlatpakBuildCommand
run = LinuxFlatpakRunCommand
package = LinuxFlatpakPackageCommand
publish = LinuxFlatpakPublishCommand
