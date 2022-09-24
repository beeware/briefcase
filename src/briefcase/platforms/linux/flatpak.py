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
from briefcase.exceptions import BriefcaseCommandError, BriefcaseConfigError
from briefcase.integrations.flatpak import Flatpak
from briefcase.platforms.linux import LinuxMixin


class LinuxFlatpakMixin(LinuxMixin):
    output_format = "flatpak"

    def binary_path(self, app):
        # Flatpak doesn't really produce an identifiable "binary" as part of its
        # build process, so the SDK wrapper creates a file that can use to identify
        # if run has been invoked. As a neat side effect, it's also a shell script
        # that can invoke the flatpak.
        return self.bundle_path(app) / f"{app.bundle}.{app.app_name}"

    def project_path(self, app):
        return self.bundle_path(app)

    def distribution_path(self, app, packaging_format):
        binary_name = app.formal_name.replace(" ", "_")
        return (
            self.platform_path
            / f"{binary_name}-{app.version}-{self.tools.host_arch}.flatpak"
        )

    def verify_tools(self):
        """Verify that we're on Linux."""
        super().verify_tools()
        if self.tools.host_os != "Linux":
            raise BriefcaseCommandError("Flatpaks can only be generated on Linux.")
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
        # Verify that either both or neither of runtime *and* sdk are specified
        try:
            runtime = app.flatpak_runtime
            if hasattr(app, "flatpak_sdk"):
                return runtime
            else:
                raise BriefcaseConfigError(
                    "If you specify a custom Flatpak runtime, "
                    "you must also specify a corresponding Flatpak SDK."
                )
        except AttributeError:
            return Flatpak.DEFAULT_RUNTIME

    def flatpak_runtime_version(self, app):
        return getattr(app, "flatpak_runtime_version", Flatpak.DEFAULT_RUNTIME_VERSION)

    def flatpak_sdk(self, app):
        # Verify that either both or neither of runtime *and* sdk are specified
        try:
            sdk = app.flatpak_sdk
            if hasattr(app, "flatpak_runtime"):
                return sdk
            else:
                raise BriefcaseConfigError(
                    "If you specify a custom Flatpak SDK, "
                    "you must also specify a corresponding Flatpak runtime."
                )
        except AttributeError:
            return Flatpak.DEFAULT_SDK


class LinuxFlatpakCreateCommand(LinuxFlatpakMixin, CreateCommand):
    description = "Create and populate a Linux Flatpak."

    def support_package_url(self, support_revision):
        """The URL of the support package to use for apps of this type.

        Flatpak uses the original CPython sources, and compiles them in
        the flatpak sandbox.
        """
        base_version = ".".join(str(m) for m in self.tools.sys.version_info[:3])
        full_version = self.tools.platform.python_version()
        return f"https://www.python.org/ftp/python/{base_version}/Python-{full_version}.tgz"

    def support_revision(self, app: AppConfig):
        """The support package revision that the template requires.

        Flatpak uses the original CPython sources, so a support revision
        isn't needed.

        :param app: The config object for the app
        :return: None; value should be ignored.
        """
        return None

    def output_format_template_context(self, app: AppConfig):
        """Add flatpak runtime/SDK details to the app template."""
        return {
            "flatpak_runtime": self.flatpak_runtime(app),
            "flatpak_runtime_version": self.flatpak_runtime_version(app),
            "flatpak_sdk": self.flatpak_sdk(app),
        }

    def install_app_support_package(self, app: AppConfig):
        """Install the support package.

        Flatpak doesn't unpack the support package; it copies the
        tarball as-is into the source tree.
        """
        support_file_path = self._download_support_package(app)
        with self.input.wait_bar("Installing support file..."):
            self.tools.shutil.copy(
                support_file_path,
                self.bundle_path(app) / support_file_path.name,
            )


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
                bundle=app.bundle,
                app_name=app.app_name,
                path=self.bundle_path(app),
            )


class LinuxFlatpakRunCommand(LinuxFlatpakMixin, RunCommand):
    description = "Run a Linux Flatpak."

    def run_app(self, app: AppConfig, **kwargs):
        """Start the application.

        :param app: The config object for the app
        """
        self.logger.info("Starting app...", prefix=app.app_name)
        self.tools.flatpak.run(
            bundle=app.bundle,
            app_name=app.app_name,
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
                bundle=app.bundle,
                app_name=app.app_name,
                version=app.version,
                build_path=self.bundle_path(app),
                output_path=self.distribution_path(app, "flatpak"),
            )


class LinuxFlatpakPublishCommand(LinuxFlatpakMixin, PublishCommand):
    description = "Publish a Linux Flatpak."


# Declare the briefcase command bindings
create = LinuxFlatpakCreateCommand  # noqa
update = LinuxFlatpakUpdateCommand  # noqa
open = LinuxFlatpakOpenCommand  # noqa
build = LinuxFlatpakBuildCommand  # noqa
run = LinuxFlatpakRunCommand  # noqa
package = LinuxFlatpakPackageCommand  # noqa
publish = LinuxFlatpakPublishCommand  # noqa
