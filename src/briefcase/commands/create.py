import hashlib
import platform
import shutil
from datetime import date
from pathlib import Path
from typing import Optional

from packaging.version import Version

import briefcase
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError, MissingNetworkResourceError
from briefcase.integrations import git
from briefcase.integrations.subprocess import NativeAppContext

from .base import (
    BaseCommand,
    TemplateUnsupportedVersion,
    UnsupportedPlatform,
    full_options,
)


class InvalidSupportPackage(BriefcaseCommandError):
    def __init__(self, filename):
        self.filename = filename
        super().__init__(f"Unable to unpack support package {filename!r}")


class MissingSupportPackage(BriefcaseCommandError):
    def __init__(self, python_version_tag, platform, host_arch):
        self.python_version_tag = python_version_tag
        self.platform = platform
        self.host_arch = host_arch
        super().__init__(
            f"""\
Unable to download {self.platform} support package for Python {self.python_version_tag} on {self.host_arch}.

This is likely because either Python {self.python_version_tag} and/or {self.host_arch}
is not yet supported on {self.platform}. You will need to:
    * Use an older version of Python; or
    * Compile your own custom support package.
"""
        )


class CreateCommand(BaseCommand):
    command = "create"

    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        self._s3 = None

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

    def icon_targets(self, app: BaseConfig):
        """Obtain the dictionary of icon targets that the template requires.

        :param app: The config object for the app
        :return: A dictionary of icons that the template supports. The keys
            of the dictionary are the size of the icons.
        """
        # If the index file hasn't been loaded for this app, load it.
        try:
            path_index = self._path_index[app]
        except KeyError:
            path_index = self._load_path_index(app)

        # If the template specifies no icons, return an empty dictionary.
        # If the template specifies a single icon without a size specification,
        #   return a dictionary with a single ``None`` key.
        # Otherwise, return the full size-keyed dictionary.
        try:
            icon_targets = path_index["icon"]
            # Convert string-specified icons into an "unknown size" icon form
            if isinstance(icon_targets, str):
                icon_targets = {None: icon_targets}
        except KeyError:
            icon_targets = {}

        return icon_targets

    def splash_image_targets(self, app: BaseConfig):
        """Obtain the dictionary of splash image targets that the template
        requires.

        :param app: The config object for the app
        :return: A dictionary of splash images that the template supports. The keys
            of the dictionary are the size of the splash images.
        """
        # If the index file hasn't been loaded for this app, load it.
        try:
            path_index = self._path_index[app]
        except KeyError:
            path_index = self._load_path_index(app)

        # If the template specifies no splash images, return an empty dictionary.
        # If the template specifies a single splash image without a size specification,
        #   return a dictionary with a single ``None`` key.
        # Otherwise, return the full size-keyed dictionary.
        try:
            splash_targets = path_index["splash"]
            # Convert string-specified splash images into an "unknown size" icon form
            if isinstance(splash_targets, str):
                splash_targets = {None: splash_targets}
        except KeyError:
            splash_targets = {}

        return splash_targets

    def document_type_icon_targets(self, app: BaseConfig):
        """Obtain the dictionary of document type icon targets that the
        template requires.

        :param app: The config object for the app
        :return: A dictionary of document types, with the values being dictionaries
            describing the icon sizes that the template supports. The inner dictionary
            describes the path fragments (relative to the bundle path) for the images
            that are required; the keys are the size of the splash images.
        """
        # If the index file hasn't been loaded for this app, load it.
        try:
            path_index = self._path_index[app]
        except KeyError:
            path_index = self._load_path_index(app)

        # If the template specifies no document types, return an empty dictionary.
        # Then, for each document type; If the template specifies a single icon
        #   without a size specification, return a dictionary with a single
        #   ``None`` key. Otherwise, return the full size-keyed dictionary.
        try:
            return {
                extension: {None: targets} if isinstance(targets, str) else targets
                for extension, targets in path_index["document_type_icon"].items()
            }

        except KeyError:
            return {}

    def output_format_template_context(self, app: BaseConfig):
        """Additional template context required by the output format.

        :param app: The config object for the app
        """
        return {}

    def generate_app_template(self, app: BaseConfig):
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
                # Properties of the generating environment
                # The full Python version string, including minor and dev/a/b/c suffixes (e.g., 3.11.0rc2)
                "python_version": platform.python_version(),
                # Transformations of explicit properties into useful forms
                "module_name": app.module_name,
                "package_name": app.package_name,
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
        try:
            with self.input.wait_bar("Unpacking support package..."):
                support_path.mkdir(parents=True, exist_ok=True)
                self.tools.shutil.unpack_archive(
                    support_file_path,
                    extract_dir=support_path,
                )
        except (shutil.ReadError, EOFError) as e:
            raise InvalidSupportPackage(support_file_path) from e

    def install_app_support_package(self, app: BaseConfig):
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

    def _download_support_package(self, app):
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
                ) from e

    def install_image(self, role, variant, size, source, target):
        """Install an icon/image of the requested size at a target location,
        using the source images defined by the app config.

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
                        source_filename = f"{source[variant]}{target.suffix}"
                        full_role = f"{variant} {role}"
                    except (TypeError, KeyError):
                        self.logger.info(
                            f"Unable to find {variant} variant for {role}; using default"
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
                        source_filename = f"{source[variant]}-{size}{target.suffix}"
                        full_role = f"{size}px {variant} {role}"
                    except (TypeError, KeyError):
                        self.logger.info(
                            f"Unable to find {size}px {variant} variant for {role}; using default"
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

    def install_app_resources(self, app: BaseConfig):
        """Install the application resources (such as icons and splash screens)
        into the bundle.

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

    def cleanup_app_content(self, app: BaseConfig):
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

        if paths_to_remove:
            with self.input.wait_bar("Removing unneeded app bundle content..."):
                for glob in paths_to_remove:
                    # Expand each glob into a full list of files that actually exist
                    # on the file system.
                    for path in self.bundle_path(app).glob(glob):
                        relative_path = path.relative_to(self.bundle_path(app))
                        if path.is_dir():
                            self.logger.info(f"Removing directory {relative_path}")
                            self.tools.shutil.rmtree(path)
                        else:
                            self.logger.info(f"Removing {relative_path}")
                            path.unlink()
        else:
            self.logger.info("No app content clean up required.")

    def create_app(self, app: BaseConfig, **options):
        """Create an application bundle.

        :param app: The config object for the app
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

        # Verify tools for the app after the app template and support package
        # are in place since the app tools may be dependent on them.
        self.verify_app_tools(app)

        self.logger.info("Installing dependencies...", prefix=app.app_name)
        self.install_app_dependencies(app=app)

        self.logger.info("Installing application code...", prefix=app.app_name)
        self.install_app_code(app=app)

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

        Raises MissingToolException if a required system tool is
        missing.
        """
        super().verify_tools()
        git.verify_git_is_installed(tools=self.tools)

    def verify_app_tools(self, app: BaseConfig):
        """Verify that tools needed to run the command for this app exist."""
        super().verify_app_tools(app)
        NativeAppContext.verify(tools=self.tools, app=app)

    def __call__(self, app: Optional[BaseConfig] = None, **options):
        # Confirm all required tools are available
        self.verify_tools()

        if app:
            state = self.create_app(app, **options)
        else:
            state = None
            for app_name, app in sorted(self.apps.items()):
                state = self.create_app(app, **full_options(state, options))

        return state
