from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

from packaging.version import Version

import briefcase
from briefcase.config import AppConfig
from briefcase.exceptions import (
    BriefcaseCommandError,
    InvalidSupportPackage,
    MissingAppSources,
    MissingNetworkResourceError,
    MissingSupportPackage,
    RequirementsInstallError,
    TemplateUnsupportedVersion,
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

    @property
    def app_template_url(self):
        """The URL for a cookiecutter repository to use when creating apps."""
        return f"https://github.com/beeware/briefcase-{self.platform}-{self.output_format}-template.git"

    def support_package_filename(self, support_revision):
        """The query arguments to use in a support package query request."""
        return f"Python-{self.python_version_tag}-{self.platform}-support.b{support_revision}.tar.gz"

    def support_package_url(self, support_revision):
        """The URL of the support package to use for apps of this type."""
        return (
            f"https://briefcase-support.s3.amazonaws.com/python/{self.python_version_tag}/{self.platform}/"
            + self.support_package_filename(support_revision)
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

    def splash_image_targets(self, app: AppConfig):
        """Obtain the dictionary of splash image targets that the template requires.

        :param app: The config object for the app
        :return: A dictionary of splash images that the template supports. The keys of
            the dictionary are the size of the splash images.
        """
        # If the template specifies no splash images, return an empty dictionary.
        # If the template specifies a single splash image without a size specification,
        #   return a dictionary with a single ``None`` key.
        # Otherwise, return the full size-keyed dictionary.
        try:
            splash_targets = self.path_index(app, "splash")
            # Convert string-specified splash images into an "unknown size" icon form
            if isinstance(splash_targets, str):
                splash_targets = {None: splash_targets}
        except KeyError:
            splash_targets = {}

        return splash_targets

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

    def output_format_template_context(self, app: AppConfig):
        """Additional template context required by the output format.

        :param app: The config object for the app
        """
        return {}

    def generate_app_template(self, app: AppConfig):
        """Create an application bundle.

        :param app: The config object for the app
        """
        # If the app config doesn't explicitly define a template,
        # use a default template.
        if app.template is None:
            template = self.app_template_url
        else:
            template = app.template

        # If the app config doesn't explicitly define a template branch,
        # use the branch derived from the Briefcase version
        version = Version(briefcase.__version__)
        if app.template_branch is None:
            template_branch = f"v{version.base_version}"
        else:
            template_branch = app.template_branch

        # Construct a template context from the app configuration.
        extra_context = app.__dict__.copy()

        # Remove the context items that describe the template
        extra_context.pop("template")
        extra_context.pop("template_branch")

        # Augment with some extra fields.
        extra_context.update(
            {
                # Ensure the output format is in the case we expect
                "format": self.output_format.lower(),
                # Properties of the generating environment
                # The full Python version string, including minor and dev/a/b/c suffixes (e.g., 3.11.0rc2)
                "python_version": platform.python_version(),
                # The host architecture
                "host_arch": self.tools.host_arch,
                # The Briefcase version
                "briefcase_version": briefcase.__version__,
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

        # Add in any extra template context required by the output format.
        extra_context.update(self.output_format_template_context(app))

        # Create the platform directory (if it doesn't already exist)
        output_path = self.bundle_path(app).parent
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            self.logger.info(
                f"Using app template: {template}, branch {template_branch}"
            )
            self.generate_template(
                template=template,
                branch=template_branch,
                output_path=output_path,
                extra_context=extra_context,
            )
        except TemplateUnsupportedVersion:
            # If we're on a development branch, and the template branch was *not*
            # provided explicitly, we can use a fallback development template.
            # Otherwise, re-raise the exception about the unsupported template version.
            if version.dev is not None and app.template_branch is None:
                # Development branches can use the main template.
                self.logger.info(
                    f"Template branch {template_branch} not found; falling back to development template"
                )
                template_branch = "main"
                self.generate_template(
                    template=template,
                    branch=template_branch,
                    output_path=output_path,
                    extra_context=extra_context,
                )
            else:
                raise

    def _unpack_support_package(self, support_file_path, support_path):
        """Unpack a support package into a specific location.

        :param support_file_path: The path to the support file to be unpacked.
        :param support_path: The path where support files should be unpacked.
        """
        # Additional protections for unpacking tar files were introduced in Python 3.12.
        # This enables the behavior that will be the default in Python 3.14.
        # However, the protections can only be enabled for tar files...not zip files.
        is_zip = support_file_path.name.endswith("zip")
        if sys.version_info >= (3, 12) and not is_zip:  # pragma: no-cover-if-lt-py312
            tarfile_kwargs = {"filter": "data"}
        else:
            tarfile_kwargs = {}

        try:
            with self.input.wait_bar("Unpacking support package..."):
                support_path.mkdir(parents=True, exist_ok=True)
                self.tools.shutil.unpack_archive(
                    support_file_path,
                    extract_dir=support_path,
                    **tarfile_kwargs,
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
        try:
            support_path = self.support_path(app)
        except KeyError:
            self.logger.info("No support package required.")
        else:
            support_file_path = self._download_support_package(app)
            self._unpack_support_package(support_file_path, support_path)

    def _download_support_package(self, app: AppConfig):
        try:
            # Work out if the app defines a custom override for
            # the support package URL.
            try:
                support_package_url = app.support_package
                custom_support_package = True
                self.logger.info(f"Using custom support package {support_package_url}")
                try:
                    # If the app has a custom support package *and* a support revision,
                    # that's an error.
                    app.support_revision
                    self.logger.warning(
                        "App specifies both a support package and a support revision; "
                        "support revision will be ignored."
                    )
                except AttributeError:
                    pass
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

                support_package_url = self.support_package_url(support_revision)
                custom_support_package = False
                self.logger.info(f"Using support package {support_package_url}")

            if support_package_url.startswith(("https://", "http://")):
                if custom_support_package:
                    # If the support package is custom, cache it using a hash of
                    # the download URL. This is needed to differentiate to support
                    # packages with the same filename, served at different URLs.
                    # (or a custom package that collides with an official package name)
                    download_path = (
                        self.data_path
                        / "support"
                        / hashlib.sha256(
                            support_package_url.encode("utf-8")
                        ).hexdigest()
                    )
                else:
                    download_path = self.data_path / "support"

                # Download the support file, caching the result
                # in the user's briefcase support cache directory.
                return self.tools.download.file(
                    url=support_package_url,
                    download_path=download_path,
                    role="support package",
                )
            else:
                return Path(support_package_url)
        except MissingNetworkResourceError as e:
            # If there is a custom support package, report the missing resource as-is.
            if custom_support_package:
                raise
            else:
                raise MissingSupportPackage(
                    python_version_tag=self.python_version_tag,
                    platform=self.platform,
                    host_arch=self.tools.host_arch,
                    is_32bit=self.tools.is_32bit_python,
                ) from e

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
                    for requirement in requires:
                        # If the requirement is a local path, convert it to
                        # absolute, because Flatpak moves the requirements file
                        # to a different place before using it.
                        if _is_local_requirement(requirement):
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
        :param progress_message: The waitbar progress message to display to the user.
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
        requires = app.requires.copy() if app.requires else []
        if test_mode and app.test_requires:
            requires.extend(app.test_requires)

        try:
            requirements_path = self.app_requirements_path(app)
            self._write_requirements_file(app, requires, requirements_path)
        except KeyError:
            try:
                app_packages_path = self.app_packages_path(app)
                self._install_app_requirements(app, requires, app_packages_path)
            except KeyError as e:
                raise BriefcaseCommandError(
                    "Application path index file does not define "
                    "`app_requirements_path` or `app_packages_path`"
                ) from e

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

        sources = app.sources.copy() if app.sources else []
        if test_mode and app.test_sources:
            sources.extend(app.test_sources)

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

        # Write the dist-info folder for the application.
        write_dist_info(
            app=app,
            dist_info_path=self.app_path(app)
            / f"{app.module_name}-{app.version}.dist-info",
        )

    def install_image(self, role, variant, size, source, target):
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
        """
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
                        self.logger.info(
                            f"Unknown variant {variant!r} for {role}; using default"
                        )
                        return
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
                        self.logger.info(
                            f"Unknown variant {variant!r} for {size}px {role}; using default"
                        )
                        return

            full_source = self.base_path / source_filename
            if full_source.exists():
                with self.input.wait_bar(
                    f"Installing {source_filename} as {full_role}..."
                ):
                    # Make sure the target directory exists
                    target.parent.mkdir(parents=True, exist_ok=True)
                    # Copy the source image to the target location
                    self.tools.shutil.copy(full_source, target)
            else:
                self.logger.info(
                    f"Unable to find {source_filename} for {full_role}; using default"
                )

    def install_app_resources(self, app: AppConfig):
        """Install the application resources (such as icons and splash screens) into the
        bundle.

        :param app: The config object for the app
        """
        for variant_or_size, targets in self.icon_targets(app).items():
            try:
                # Treat the targets as a dictionary of sizes;
                # if there's no `items`, then it's an icon without variants.
                for size, target in targets.items():
                    self.install_image(
                        "application icon",
                        source=app.icon,
                        variant=variant_or_size,
                        size=size,
                        target=self.bundle_path(app) / target,
                    )
            except AttributeError:
                # Either a single variant, or a single size.
                self.install_image(
                    "application icon",
                    source=app.icon,
                    variant=None,
                    size=variant_or_size,
                    target=self.bundle_path(app) / targets,
                )

        for variant_or_size, targets in self.splash_image_targets(app).items():
            try:
                # Treat the targets as a dictionary of sizes;
                # if there's no `items`, then it's a splash without variants
                for size, target in targets.items():
                    self.install_image(
                        "splash image",
                        source=app.splash,
                        variant=variant_or_size,
                        size=size,
                        target=self.bundle_path(app) / target,
                    )
            except AttributeError:
                # Either a single variant, or a single size.
                self.install_image(
                    "splash image",
                    source=app.splash,
                    variant=None,
                    size=variant_or_size,
                    target=self.bundle_path(app) / targets,
                )

        for extension, doctype in self.document_type_icon_targets(app).items():
            for size, target in doctype.items():
                self.install_image(
                    f"icon for .{extension} documents",
                    size=size,
                    source=app.document_types[extension]["icon"],
                    variant=None,
                    target=self.bundle_path(app) / target,
                )

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
                        if self.logger.verbosity >= 1:
                            self.logger.info(f"Removing directory {relative_path}")
                        self.tools.shutil.rmtree(path)
                    else:
                        if self.logger.verbosity >= 1:
                            self.logger.info(f"Removing {relative_path}")
                        path.unlink()

    def create_app(self, app: AppConfig, test_mode: bool = False, **options):
        """Create an application bundle.

        :param app: The config object for the app
        :param test_mode: Should the app be updated in test mode? (default: False)
        """
        if not app.supported:
            raise UnsupportedPlatform(self.platform)

        bundle_path = self.bundle_path(app)
        if bundle_path.exists():
            self.logger.info()
            confirm = self.input.boolean_input(
                f"Application {app.app_name!r} already exists; overwrite", default=False
            )
            if not confirm:
                self.logger.error(
                    f"Aborting creation of app {app.app_name!r}; existing application will not be overwritten."
                )
                return
            self.logger.info("Removing old application bundle...", prefix=app.app_name)
            self.tools.shutil.rmtree(bundle_path)

        self.logger.info("Generating application template...", prefix=app.app_name)
        self.generate_app_template(app=app)

        self.logger.info("Installing support package...", prefix=app.app_name)
        self.install_app_support_package(app=app)

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

    def __call__(self, app: AppConfig | None = None, **options) -> dict | None:
        # Confirm host compatibility, that all required tools are available,
        # and that the app configuration is finalized.
        self.finalize(app)

        if app:
            state = self.create_app(app, **options)
        else:
            state = None
            for app_name, app in sorted(self.apps.items()):
                state = self.create_app(app, **full_options(state, options))

        return state


def _has_url(requirement):
    """Determine if the requirement is defined as a URL.

    Detects any of the URL schemes supported by pip
    (https://pip.pypa.io/en/stable/topics/vcs-support/).

    :param requirement: The requirement to check
    :returns: True if the requirement is a URL supported by pip.
    """
    return any(
        f"{scheme}:" in requirement
        for scheme in (
            ["http", "https", "file", "ftp"]
            + ["git+file", "git+https", "git+ssh", "git+http", "git+git", "git"]
            + ["hg+file", "hg+http", "hg+https", "hg+ssh", "hg+static-http"]
            + ["svn", "svn+svn", "svn+http", "svn+https", "svn+ssh"]
            + ["bzr+http", "bzr+https", "bzr+ssh", "bzr+sftp", "bzr+ftp", "bzr+lp"]
        )
    )


def _is_local_requirement(requirement):
    """Determine if the requirement is a local file path.

    :param requirement: The requirement to check
    :returns: True if the requirement is a local file path
    """
    # Windows allows both / and \ as a path separator in requirements.
    separators = [os.sep]
    if os.altsep:
        separators.append(os.altsep)

    return any(sep in requirement for sep in separators) and (not _has_url(requirement))
