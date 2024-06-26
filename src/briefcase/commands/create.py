from __future__ import annotations

import contextlib
import hashlib
import os
import platform
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import briefcase
from briefcase.commands.base import is_local_requirement
from briefcase.config import AppConfig
from briefcase.exceptions import (
    BriefcaseCommandError,
    InvalidStubBinary,
    InvalidSupportPackage,
    MissingAppSources,
    MissingNetworkResourceError,
    MissingStubBinary,
    MissingSupportPackage,
    RequirementsInstallError,
    UnsupportedPlatform,
)
from briefcase.integrations.git import Git
from briefcase.integrations.subprocess import NativeAppContext

from .base import BaseCommand, full_options


def cookiecutter_cache_path(template):
    """Determine the cookiecutter template cache directory given a template URL.

    This will return a valid path, regardless of whether `template`

    :param template: The template to use. This can be a filesystem path or
        a URL.
    :returns: The path that cookiecutter would use for the given template name.
    """
    template = template.rstrip("/")
    tail = template.split("/")[-1]
    cache_name = tail.rsplit(".git")[0]
    return Path.home() / ".cookiecutters" / cache_name


def write_dist_info(app: AppConfig, dist_info_path: Path):
    """Install the dist-info folder for the application.

    :param app: The config object for the app
    :param dist_info_path: The path into which the dist-info folder should be written.
    """
    # Create dist-info folder, and write a minimal metadata collection.
    dist_info_path.mkdir(exist_ok=True)
    with (dist_info_path / "INSTALLER").open("w", encoding="utf-8") as f:
        f.write("briefcase\n")
    with (dist_info_path / "WHEEL").open("w", encoding="utf-8") as f:
        f.write("Wheel-Version: 1.0\n")
        f.write("Root-Is-Purelib: true\n")
        f.write(f"Generator: briefcase ({briefcase.__version__})\n")
        f.write("Tag: py3-none-any\n")
    with (dist_info_path / "METADATA").open("w", encoding="utf-8") as f:
        f.write("Metadata-Version: 2.1\n")
        f.write(f"Briefcase-Version: {briefcase.__version__}\n")
        f.write(f"Name: {app.app_name}\n")
        f.write(f"Formal-Name: {app.formal_name}\n")
        f.write(f"App-ID: {app.bundle_identifier}\n")
        f.write(f"Version: {app.version}\n")
        if app.url:
            f.write(f"Home-page: {app.url}\n")
            f.write(f"Download-URL: {app.url}\n")
        else:
            f.write("Download-URL: \n")
        if app.author:
            f.write(f"Author: {app.author}\n")
        if app.author_email:
            f.write(f"Author-email: {app.author_email}\n")
        f.write(f"Summary: {app.description}\n")
    with (dist_info_path / "top_level.txt").open("w", encoding="utf-8") as f:
        f.write(f"{app.module_name}\n")


class CreateCommand(BaseCommand):
    command = "create"
    description = "Create a new app for a target platform."

    # app properties that won't be exposed to the context
    hidden_app_properties = {"permission"}

    @property
    def app_template_url(self) -> str:
        """The URL for a cookiecutter repository to use when creating apps."""
        return f"https://github.com/beeware/briefcase-{self.platform}-{self.output_format}-template.git"

    def support_package_filename(self, support_revision: str) -> str:
        """The query arguments to use in a support package query request."""
        return f"Python-{self.python_version_tag}-{self.platform}-support.b{support_revision}.tar.gz"

    def support_package_url(self, support_revision: str) -> str:
        """The URL of the support package to use for apps of this type."""
        return (
            "https://briefcase-support.s3.amazonaws.com/python/"
            f"{self.python_version_tag}/"
            f"{self.platform}/"
            f"{self.support_package_filename(support_revision)}"
        )

    def stub_binary_filename(self, support_revision: str, is_console_app: bool) -> str:
        """The filename for the stub binary."""
        stub_type = "Console" if is_console_app else "GUI"
        return f"{stub_type}-Stub-{self.python_version_tag}-b{support_revision}.zip"

    def stub_binary_url(self, support_revision: str, is_console_app: bool) -> str:
        """The URL of the stub binary to use for apps of this type."""
        return (
            "https://briefcase-support.s3.amazonaws.com/python/"
            f"{self.python_version_tag}/"
            f"{self.platform}/"
            f"{self.stub_binary_filename(support_revision, is_console_app)}"
        )

    def icon_targets(self, app: AppConfig):
        """Obtain the dictionary of icon targets that the template requires.

        :param app: The config object for the app
        :return: A dictionary of icons that the template supports. The keys of the
            dictionary are the size of the icons.
        """
        # If the template specifies no icons, return an empty dictionary.
        # If the template specifies a single icon without a size specification,
        #   return a dictionary with a single ``None`` key.
        # Otherwise, return the full size-keyed dictionary.
        try:
            icon_targets = self.path_index(app, "icon")
            # Convert string-specified icons into an "unknown size" icon form
            if isinstance(icon_targets, str):
                icon_targets = {None: icon_targets}
        except KeyError:
            icon_targets = {}

        return icon_targets

    def document_type_icon_targets(self, app: AppConfig):
        """Obtain the dictionary of document type icon targets that the template
        requires.

        :param app: The config object for the app
        :return: A dictionary of document types, with the values being dictionaries
            describing the icon sizes that the template supports. The inner dictionary
            describes the path fragments (relative to the bundle path) for the images
            that are required; the keys are the size of the splash images.
        """
        # If the template specifies no document types, return an empty dictionary.
        # Then, for each document type; If the template specifies a single icon
        #   without a size specification, return a dictionary with a single
        #   ``None`` key. Otherwise, return the full size-keyed dictionary.
        try:
            icon_targets = self.path_index(app, "document_type_icon")
            return {
                extension: {None: targets} if isinstance(targets, str) else targets
                for extension, targets in icon_targets.items()
            }

        except KeyError:
            return {}

    def _x_permissions(self, app: AppConfig):
        """Extract the known cross-platform permission definitions from the app's
        permissions definitions.

        After calling this method, the ``permissions`` declaration for the app will
        only contain keys that are *not* cross-platform keys.

        :param app: The config object for the app
        :returns: A dictionary of known cross-platform permission definitions.
        """
        return {
            key: app.permission.pop(key, None)
            for key in [
                "camera",
                "microphone",
                "coarse_location",
                "fine_location",
                "background_location",
                "photo_library",
            ]
        }

    def permissions_context(self, app: AppConfig, x_permissions: dict[str, str]):
        """Additional template context for permissions.

        :param app: The config object for the app
        :param x_permissions: The dictionary of known cross-platform permission
            definitions.
        :returns: The template context describing permissions for the app.
        """
        return {}

    def output_format_template_context(self, app: AppConfig):
        """Additional template context required by the output format.

        :param app: The config object for the app
        """
        return {}

    def generate_app_template(self, app: AppConfig):
        """Create an application bundle.

        :param app: The config object for the app
        """
        # Construct a template context from the app configuration.
        extra_context = {
            key: value
            for key, value in app.__dict__.items()
            if key not in self.hidden_app_properties
        }

        # Remove the context items that describe the template
        extra_context.pop("template")
        extra_context.pop("template_branch")

        # Augment with some extra fields
        extra_context.update(
            {
                # Ensure the output format is in the case we expect
                "format": self.output_format.lower(),
                # Properties of the generating environment
                # The full Python version string, including minor and dev/a/b/c suffixes (e.g., 3.11.0rc2)
                "python_version": platform.python_version(),
                # The host architecture
                "host_arch": self.tools.host_arch,
                # Transformations of explicit properties into useful forms
                "class_name": app.class_name,
                "module_name": app.module_name,
                "package_name": app.package_name,
                "bundle_identifier": app.bundle_identifier,
                # Properties that are a function of the execution
                "year": date.today().strftime("%Y"),
                "month": date.today().strftime("%B"),
            }
        )

        # Add in any extra template context to support permissions
        extra_context.update(self.permissions_context(app, self._x_permissions(app)))

        # Add in any extra template context required by the output format
        extra_context.update(self.output_format_template_context(app))

        # Create the platform directory (if it doesn't already exist)
        output_path = self.bundle_path(app).parent
        output_path.mkdir(parents=True, exist_ok=True)

        self.generate_template(
            template=app.template if app.template else self.app_template_url,
            branch=app.template_branch,
            output_path=output_path,
            extra_context=extra_context,
        )

    def _unpack_support_package(self, support_file_path: Path, support_path: Path):
        """Unpack a support package into a specific location.

        :param support_file_path: The path to the support file to be unpacked.
        :param support_path: The path where support files should be unpacked.
        """
        try:
            with self.input.wait_bar("Unpacking support package..."):
                support_path.mkdir(parents=True, exist_ok=True)
                self.tools.file.unpack_archive(
                    support_file_path,
                    extract_dir=support_path,
                )
        except (shutil.ReadError, EOFError) as e:
            raise InvalidSupportPackage(support_file_path) from e

    def _cleanup_app_support_package(self, support_path):
        """The internal implementation of the app support cleanup method.

        Guaranteed to only be invoked if the backend uses a support package, and the
        support path exists.

        :param support_path: The support path to clean up.
        """
        with self.input.wait_bar("Removing existing support package..."):
            self.tools.shutil.rmtree(support_path)

    def cleanup_app_support_package(self, app: AppConfig):
        """Clean up an existing application support package.

        :param app: The config object for the app
        """
        try:
            support_path = self.support_path(app)
        except KeyError:
            # No cleanup required.
            pass
        else:
            if support_path.exists():
                self._cleanup_app_support_package(support_path)

    def install_app_support_package(self, app: AppConfig):
        """Install the application support package.

        :param app: The config object for the app
        """
        support_install_path, support_url, custom = self._app_support_package(app)

        if support_install_path is None:
            self.logger.info("No support package required.")
            self.tracking_add_support_package(app, support_url="")
        else:
            self.logger.info(
                f"Using{' custom' if custom else ''} support package {support_url}"
            )
            support_file_path = self._resolve_support_package_url(support_url, custom)
            self._unpack_support_package(support_file_path, support_install_path)
            self.tracking_add_support_package(app, support_url=support_url)

    def _app_support_package(
        self,
        app: AppConfig,
        warn_user: bool = True,
    ) -> tuple[Path | None, str, bool]:
        """Derive support package download and install locations.

        Raises MissingSupportPackage if app does not define a support package.

        :param app: The config object for the app
        :param warn_user: Disable warnings for ignored app support configuration
        :returns: A tuple of the:
            [0] ``Path`` where the support package should be installed; will be ``None``
                if the app does not require a support package
            [1] string for filesystem path or URL for support package archive
            [2] ``True``/``False`` for whether the support package is custom and not
                the Briefcase-provided package
        """
        # If the app does not define a filesystem location to install the support
        # package in to the app, one is not required
        try:
            support_path = self.support_path(app)
        except KeyError:
            return None, "", False

        try:
            support_url = app.support_package
            custom_support = True
            if warn_user:
                with contextlib.suppress(AttributeError):
                    # If the app has a custom support package *and* a support revision,
                    # that's an error.
                    app.support_revision
                    self.logger.warning(
                        "App specifies both a support package and a support revision; "
                        "support revision will be ignored."
                    )
        except AttributeError:
            # If the app specifies a support revision, use it;
            # otherwise, use the support revision named by the template
            try:
                support_revision = app.support_revision
            except AttributeError:
                # No support revision specified; use the template-specified version
                try:
                    support_revision = self.support_revision(app)
                except KeyError:
                    # No template-specified support revision
                    raise MissingSupportPackage(
                        python_version_tag=self.python_version_tag,
                        platform=self.platform,
                        host_arch=self.tools.host_arch,
                        is_32bit=self.tools.is_32bit_python,
                    )

            support_url = self.support_package_url(support_revision)
            custom_support = False

        return support_path, support_url, custom_support

    def _resolve_support_package_url(self, support_url: str, custom: bool) -> Path:
        """Resolve a filesystem location for the support package.

        The support package for an app can be either a remote HTTP resource or a local
        filesystem path. If the support package is a remote address, the archive is
        downloaded and cached in the Briefcase data directory.

        :param support_url: URL or filepath to support package
        :param custom: ``True`` if user is not using a Briefcase-provided support package
        :returns: ``Path`` for archive of support package to install in to the app
        """
        if support_url.startswith(("https://", "http://")):
            if custom:
                # If the support package is custom, cache it using a hash of
                # the download URL. This is needed to differentiate to support
                # packages with the same filename, served at different URLs.
                # (or a custom package that collides with an official package name)
                download_path = (
                    self.data_path
                    / "support"
                    / hashlib.sha256(support_url.encode("utf-8")).hexdigest()
                )
            else:
                download_path = self.data_path / "support"

            try:
                # Download the support file, caching the result
                # in the user's briefcase support cache directory.
                return self.tools.file.download(
                    url=support_url,
                    download_path=download_path,
                    role="support package",
                )
            except MissingNetworkResourceError as e:
                # If there is a custom support package, report the missing resource as-is.
                if custom:
                    raise
                else:
                    raise MissingSupportPackage(
                        python_version_tag=self.python_version_tag,
                        platform=self.platform,
                        host_arch=self.tools.host_arch,
                        is_32bit=self.tools.is_32bit_python,
                    ) from e

        else:
            return Path(support_url)

    def cleanup_stub_binary(self, app: AppConfig):
        """Clean up an existing application support package.

        :param app: The config object for the app
        """
        with self.input.wait_bar("Removing existing stub binary..."):
            self.binary_executable_path(app).unlink(missing_ok=True)
            self.unbuilt_executable_path(app).unlink(missing_ok=True)

    def install_stub_binary(self, app: AppConfig):
        """Install the application stub binary into the "unbuilt" location.

        :param app: The config object for the app
        """
        # If the platform uses a stub binary, the template will define a binary
        # revision. If this template configuration item doesn't exist, no stub
        # binary is required.
        try:
            self.stub_binary_revision(app)
        except KeyError:
            return

        self.logger.info("Installing stub binary...", prefix=app.app_name)

        stub_install_path, stub_url, custom_stub = self._stub_binary(app)
        stub_binary_path = self._resolve_stub_binary_url(stub_url, custom_stub)

        with self.input.wait_bar("Installing stub binary..."):
            self.logger.info(f"Using stub binary {stub_url}")
            # Ensure the folder for the stub binary exists
            stub_install_path.parent.mkdir(exist_ok=True, parents=True)

            # Install the stub binary into the unbuilt location.
            # Allow for both raw and compressed artefacts.
            try:
                if self.tools.file.is_archive(stub_binary_path):
                    self.tools.file.unpack_archive(
                        stub_binary_path,
                        extract_dir=stub_install_path.parent,
                    )
                elif stub_binary_path.is_file():
                    self.tools.shutil.copyfile(stub_binary_path, stub_install_path)
                else:
                    raise InvalidStubBinary(stub_binary_path)
            except (shutil.ReadError, EOFError, OSError) as e:
                raise InvalidStubBinary(stub_binary_path) from e
            else:
                # Ensure the binary is executable
                self.tools.os.chmod(stub_install_path, 0o755)

            self.tracking_add_stub_binary(app, stub_binary_url=stub_url)

    def _stub_binary(
        self,
        app: AppConfig,
        warn_user: bool = True,
    ) -> tuple[Path, str, bool]:
        """Derive stub binary download and install locations.

        :param app: The config object for the app
        :param warn_user: Disable warnings for ignored stub binary configuration
        :returns: A tuple of the:
            [0] ``Path`` where the stub binary should be installed
            [1] string for filesystem path or URL for stub binary archive/file
            [2] ``True``/``False`` for whether the stub binary is custom and not
                the Briefcase-provided package
        """
        stub_install_path = self.unbuilt_executable_path(app)

        try:
            stub_url: str = app.stub_binary
            custom_stub = True
            if warn_user:
                with contextlib.suppress(AttributeError):
                    # If the app has a custom stub binary *and* a support revision,
                    # that's an error.
                    app.stub_binary_revision
                    self.logger.warning(
                        "App specifies both a stub binary and a stub binary revision; "
                        "stub binary revision will be ignored."
                    )
        except AttributeError:
            # If the app specifies a support revision, use it; otherwise, use the
            # support revision named by the template. This value *must* exist, as
            # stub binary handling won't be triggered at all unless it is present.
            try:
                stub_binary_revision = app.stub_binary_revision
            except AttributeError:
                stub_binary_revision = self.stub_binary_revision(app)

            stub_url = self.stub_binary_url(stub_binary_revision, app.console_app)
            custom_stub = False

        return stub_install_path, stub_url, custom_stub

    def _resolve_stub_binary_url(self, stub_binary_url: str, custom_stub_binary: bool):
        if stub_binary_url.startswith(("https://", "http://")):
            if custom_stub_binary:
                # If the support package is custom, cache it using a hash of
                # the download URL. This is needed to differentiate to support
                # packages with the same filename, served at different URLs.
                # (or a custom package that collides with an official package name)
                download_path = (
                    self.data_path
                    / "stub"
                    / hashlib.sha256(stub_binary_url.encode("utf-8")).hexdigest()
                )
            else:
                download_path = self.data_path / "stub"

            try:
                # Download the stub binary, caching the result
                # in the user's briefcase stub cache directory.
                return self.tools.file.download(
                    url=stub_binary_url,
                    download_path=download_path,
                    role="stub binary",
                )
            except MissingNetworkResourceError as e:
                # If there is a custom support package, report the missing resource as-is.
                if custom_stub_binary:
                    raise
                else:
                    raise MissingStubBinary(
                        python_version_tag=self.python_version_tag,
                        platform=self.platform,
                        host_arch=self.tools.host_arch,
                        is_32bit=self.tools.is_32bit_python,
                    ) from e
        else:
            return Path(stub_binary_url)

    def _write_requirements_file(
        self,
        app: AppConfig,
        requires: list[str],
        requirements_path: Path,
    ):
        """Configure application requirements by writing a requirements.txt file.

        :param app: The app configuration
        :param requires: The full list of requirements
        :param requirements_path: The full path to a requirements.txt file that will be
            written.
        """
        with self.input.wait_bar("Writing requirements file..."):
            with requirements_path.open("w", encoding="utf-8") as f:
                if requires:
                    # Add timestamp so build systems (such as Gradle) detect a change
                    # in the file and perform a re-installation of all requirements.
                    f.write(f"# Generated {datetime.now()}\n")
                    for requirement in requires:
                        # If the requirement is a local path, convert it to
                        # absolute, because Flatpak moves the requirements file
                        # to a different place before using it.
                        if is_local_requirement(requirement):
                            # We use os.path.abspath() rather than Path.resolve()
                            # because we *don't* want Path's symlink resolving behavior.
                            requirement = os.path.abspath(self.base_path / requirement)
                        f.write(f"{requirement}\n")

    def _pip_requires(self, app: AppConfig, requires: list[str]):
        """Convert the list of requirements to be passed to pip into its final form.

        :param app: The app configuration
        :param requires: The user-specified list of app requirements
        :returns: The final list of requirement arguments to pass to pip
        """
        return requires

    def _extra_pip_args(self, app: AppConfig):
        """Any additional arguments that must be passed to pip when installing packages.

        :param app: The app configuration
        :returns: A list of additional arguments
        """
        return []

    def _pip_install(
        self,
        app: AppConfig,
        app_packages_path: Path,
        pip_args: list[str],
        install_hint: str = "",
        **pip_kwargs,
    ):
        """Invoke pip to install a set of requirements.

        :param app: The app configuration
        :param app_packages_path: The full path of the app_packages folder into which
            requirements should be installed.
        :param pip_args: The list of arguments (including the list of requirements to
            install) to pass to pip. This is in addition to the default arguments that
            disable pip version checks, forces upgrades, and installs into the nominated
            ``app_packages`` path.
        :param install_hint: Additional hint information to provide in the exception
            message if the pip install call fails.
        :param pip_kwargs: Any additional keyword arguments to pass to ``subprocess.run``
            when invoking pip.
        """
        try:
            self.tools[app].app_context.run(
                [
                    sys.executable,
                    "-u",
                    "-X",
                    "utf8",
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--no-python-version-warning",
                    "--upgrade",
                    "--no-user",
                    f"--target={app_packages_path}",
                ]
                + (["-vv"] if self.logger.is_deep_debug else [])
                + self._extra_pip_args(app)
                + pip_args,
                check=True,
                encoding="UTF-8",
                **pip_kwargs,
            )
        except subprocess.CalledProcessError as e:
            raise RequirementsInstallError(install_hint=install_hint) from e

    def _install_app_requirements(
        self,
        app: AppConfig,
        requires: list[str],
        app_packages_path: Path,
        progress_message: str = "Installing app requirements...",
        pip_kwargs: dict[str, str] | None = None,
    ):
        """Install requirements for the app with pip.

        :param app: The app configuration
        :param requires: The list of requirements to install
        :param app_packages_path: The full path of the app_packages folder into which
            requirements should be installed.
        :param progress_message: The Wait Bar progress message to display to the user.
        :param pip_kwargs: Any additional keyword arguments to pass to the subprocess
            when invoking pip.
        """
        # Clear existing dependency directory
        if app_packages_path.is_dir():
            self.tools.shutil.rmtree(app_packages_path)
            self.tools.os.mkdir(app_packages_path)

        # Install requirements
        if requires:
            with self.input.wait_bar(progress_message):
                self._pip_install(
                    app,
                    app_packages_path=app_packages_path,
                    pip_args=self._pip_requires(app, requires),
                    **(pip_kwargs if pip_kwargs else {}),
                )
        else:
            self.logger.info("No application requirements.")

    def install_app_requirements(self, app: AppConfig, test_mode: bool):
        """Handle requirements for the app.

        This will result in either (in preferential order):
         * a requirements.txt file being written at a location specified by
           ``app_requirements_path`` in the template path index
         * requirements being installed with pip into the location specified
           by the ``app_packages_path`` in the template path index.

        If ``test_mode`` is True, the test requirements will also be installed.

        If the path index doesn't specify either of the path index entries,
        an error is raised.

        :param app: The config object for the app
        :param test_mode: Should the test requirements be installed?
        """
        requires = app.requires(test_mode=test_mode)

        requirements_path = app_packages_path = None
        try:
            requirements_path = self.app_requirements_path(app)
        except KeyError:
            try:
                app_packages_path = self.app_packages_path(app)
            except KeyError as e:
                raise BriefcaseCommandError(
                    "Application path index file does not define "
                    "`app_requirements_path` or `app_packages_path`"
                ) from e

        if requirements_path:
            self._write_requirements_file(app, requires, requirements_path)
        else:
            try:
                self._install_app_requirements(app, requires, app_packages_path)
            except BaseException:
                # Installing the app's requirements will delete any currently installed
                # requirements; so, if anything goes wrong, clear the tracking info to
                # ensure the requirements are installed on the next run.
                self.tracking_add_requirements(app, requires=[])
                raise
            else:
                self.tracking_add_requirements(app, requires=requires)

    def install_app_code(self, app: AppConfig, test_mode: bool):
        """Install the application code into the bundle.

        :param app: The config object for the app
        :param test_mode: Should the application test code also be installed?
        """
        # Remove existing app folder if it exists
        app_path = self.app_path(app)
        if app_path.exists():
            self.tools.shutil.rmtree(app_path)
        self.tools.os.mkdir(app_path)

        sources = app.sources(test_mode=test_mode)

        # Install app code.
        if sources:
            for src in sources:
                with self.input.wait_bar(f"Installing {src}..."):
                    original = self.base_path / src
                    target = app_path / original.name

                    # Install the new copy of the app code.
                    if not original.exists():
                        raise MissingAppSources(src)
                    elif original.is_dir():
                        self.tools.shutil.copytree(original, target)
                    else:
                        self.tools.shutil.copy(original, target)
        else:
            self.logger.info(f"No sources defined for {app.app_name}.")

        self.tracking_add_sources(app, sources=sources)

        # Write the dist-info folder for the application
        write_dist_info(app=app, dist_info_path=self.dist_info_path(app))

    def install_app_resources(self, app: AppConfig):
        """Install the application resources (such as icons and splash screens) into the
        bundle.

        :param app: The config object for the app
        """
        resources = self._resolve_app_resources(app, do_install=True)
        self.tracking_add_resources(app, resources=resources.values())

    def _resolve_app_resources(
        self,
        app: AppConfig,
        do_install: bool = True,
    ) -> dict[str, Path]:
        """Resolve app resource files to their targets."""
        resource_map = {}

        for variant_or_size, targets in self.icon_targets(app).items():
            try:
                # Treat the targets as a dictionary of sizes;
                # if there's no `items`, then it's an icon without variants.
                for size, target in targets.items():
                    resource_map.update(
                        self._resolve_image(
                            "application icon",
                            source=app.icon,
                            variant=variant_or_size,
                            size=size,
                            target=self.bundle_path(app) / target,
                            do_install=do_install,
                        )
                    )
            except AttributeError:
                # Either a single variant, or a single size.
                resource_map.update(
                    self._resolve_image(
                        "application icon",
                        source=app.icon,
                        variant=None,
                        size=variant_or_size,
                        target=self.bundle_path(app) / targets,
                        do_install=do_install,
                    )
                )

        # Briefcase v0.3.18 - splash screens deprecated.
        if getattr(app, "splash", None) and do_install:
            self.logger.warning()
            self.logger.warning(
                "Splash screens are now configured based on the icon. "
                "The splash configuration will be ignored."
            )

        for extension, doctype in self.document_type_icon_targets(app).items():
            self.logger.info()
            for size, target in doctype.items():
                resource_map.update(
                    self._resolve_image(
                        f"icon for .{extension} documents",
                        size=size,
                        source=app.document_types[extension]["icon"],
                        variant=None,
                        target=self.bundle_path(app) / target,
                        do_install=do_install,
                    )
                )

        return resource_map

    def _resolve_image(
        self, role, variant, size, source, target, do_install=True
    ) -> dict[str, Path]:
        """Install an icon/image of the requested size at a target location, using the
        source images defined by the app config.

        :param role: A string describing the role the of the image.
        :param variant: The image variant. A variant of ``None`` means the image
            has no variants
        :param size: The requested size for the image. A size of
            ``None`` means the largest available size should be used.
        :param source: The image source; or a dictionary of sources for each
            variant. The sources will *not* include any extension or size
            modifier; these will be added based on the requested target and
            variant.
        :param target: The full path where the image should be installed.
        :param do_install: Copy image in to the app bundle
        """
        image = {}

        if source is not None:
            if size is None:
                if variant is None:
                    source_filename = f"{source}{target.suffix}"
                    full_role = role
                else:
                    try:
                        full_role = f"{variant} {role}"
                        source_filename = f"{source[variant]}{target.suffix}"
                    except TypeError:
                        source_filename = f"{source}-{variant}{target.suffix}"
                    except KeyError:
                        if do_install:
                            self.logger.info(
                                f"Unknown variant {variant!r} for {role}; using default"
                            )
            else:
                if variant is None:
                    # An annoying edge case is the case of an unsized variant.
                    # In that case, `size` is actually the variant, and the
                    # source is a dictionary keyed by variant. Try that
                    # lookup; if it fails, we have a sized image with no
                    # variant.
                    try:
                        source_filename = f"{source[size]}{target.suffix}"
                        full_role = f"{size} {role}"
                    except TypeError:
                        # The lookup on the source failed; that means we
                        # have a sized image without variants.
                        source_filename = f"{source}-{size}{target.suffix}"
                        full_role = f"{size}px {role}"
                else:
                    try:
                        full_role = f"{size}px {variant} {role}"
                        source_filename = f"{source[variant]}-{size}{target.suffix}"
                    except TypeError:
                        source_filename = f"{source}-{variant}-{size}{target.suffix}"
                    except KeyError:
                        if do_install:
                            self.logger.info(
                                f"Unknown variant {variant!r} for {size}px {role}; using default"
                            )

            if (full_source := self.base_path / source_filename).exists():
                if do_install:
                    with self.input.wait_bar(
                        f"Installing {source_filename} as {full_role}..."
                    ):
                        # Make sure the target directory exists
                        target.parent.mkdir(parents=True, exist_ok=True)
                        # Copy the source image to the target location
                        self.tools.shutil.copy(full_source, target)
                image[full_role] = full_source
            else:
                if do_install:
                    self.logger.info(
                        f"Unable to find {source_filename} for {full_role}; using default"
                    )

        return image

    def cleanup_app_content(self, app: AppConfig):
        """Remove any content not needed by the final app bundle.

        :param app: The config object for the app
        """
        try:
            # Retrieve any cleanup paths defined by the app template
            paths_to_remove = self.cleanup_paths(app)
        except KeyError:
            paths_to_remove = []

        try:
            # Add any user-specified paths, expanded using the app as template context.
            paths_to_remove.extend([glob.format(app=app) for glob in app.cleanup_paths])
        except AttributeError:
            pass

        # Remove __pycache__ folders. These folders might contain stale PYC
        # artefacts, or encode file paths that reflect the original source
        # location. The stub binaries all disable PYC generation, to avoid
        # corrupting any app bundle signatures.
        paths_to_remove.append("**/__pycache__")

        with self.input.wait_bar("Removing unneeded app bundle content..."):
            for glob in paths_to_remove:
                # Expand each glob into a full list of files that actually exist
                # on the file system.
                for path in self.bundle_path(app).glob(glob):
                    relative_path = path.relative_to(self.bundle_path(app))
                    if path.is_dir():
                        self.logger.verbose(f"Removing directory {relative_path}")
                        self.tools.shutil.rmtree(path)
                    else:
                        self.logger.verbose(f"Removing {relative_path}")
                        path.unlink()

    def update_tracking(self, app: AppConfig):
        """Updates the tracking database when an app is successfully created."""
        self.tracking_add_created_instant(app)
        self.tracking_add_briefcase_version(app)
        self.tracking_add_python_env(app)
        self.tracking_add_metadata(app)

    def create_app(
        self,
        app: AppConfig,
        test_mode: bool = False,
        force: bool = False,
        **options,
    ):
        """Create an application bundle.

        :param app: The config object for the app
        :param test_mode: Should the app be updated in test mode? (default: False)
        :param force: Should the app be created if it already exists? (default: False)
        """
        if not app.supported:
            raise UnsupportedPlatform(self.platform)

        bundle_path = self.bundle_path(app)

        if bundle_path.exists():
            if not force:
                self.logger.info()
                if not self.input.boolean_input(
                    f"Application {app.app_name!r} already exists; overwrite",
                    default=False,
                ):
                    raise BriefcaseCommandError(
                        f"Aborting re-creation of app {app.app_name!r}",
                        skip_logfile=True,
                    )
            self.logger.info("Removing old application bundle...", prefix=app.app_name)
            self.tools.shutil.rmtree(bundle_path)

        self.logger.info("Generating application template...", prefix=app.app_name)
        self.generate_app_template(app=app)

        self.logger.info("Installing support package...", prefix=app.app_name)
        self.install_app_support_package(app=app)

        self.install_stub_binary(app=app)

        # Verify the app after the app template and support package
        # are in place since the app tools may be dependent on them.
        self.verify_app(app)

        self.logger.info("Installing application code...", prefix=app.app_name)
        self.install_app_code(app=app, test_mode=test_mode)

        self.logger.info("Installing requirements...", prefix=app.app_name)
        self.install_app_requirements(app=app, test_mode=test_mode)

        self.logger.info("Installing application resources...", prefix=app.app_name)
        self.install_app_resources(app=app)

        self.logger.info("Removing unneeded app content...", prefix=app.app_name)
        self.cleanup_app_content(app=app)

        self.update_tracking(app=app)

        self.logger.info(
            f"Created {bundle_path.relative_to(self.base_path)}",
            prefix=app.app_name,
        )

    def verify_tools(self):
        """Verify that the tools needed to run this command exist.

        Raises MissingToolException if a required system tool is missing.
        """
        super().verify_tools()
        Git.verify(tools=self.tools)

    def verify_app_tools(self, app: AppConfig):
        """Verify that tools needed to run the command for this app exist."""
        super().verify_app_tools(app)
        NativeAppContext.verify(tools=self.tools, app=app)

    def __call__(
        self,
        app: AppConfig | None = None,
        **options,
    ) -> dict | None:
        # Finish preparing the AppConfigs and run final checks required to for command
        self.finalize(app)

        if app:
            state = self.create_app(app, **options)
        else:
            state = None
            for app_name, app in sorted(self.apps.items()):
                state = self.create_app(app, **full_options(state, options))

        return state
