import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from cookiecutter import exceptions as cookiecutter_exceptions
from requests import exceptions as requests_exceptions

import briefcase
from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError, NetworkFailure

from .base import (
    BaseCommand,
    TemplateUnsupportedVersion,
    UnsupportedPlatform,
    full_options
)


class InvalidTemplateRepository(BriefcaseCommandError):
    def __init__(self, template):
        self.template = template
        super().__init__(
            'Unable to clone application template; is the template path {template!r} correct?'.format(
                template=template
            )
        )


class InvalidSupportPackage(BriefcaseCommandError):
    def __init__(self, filename):
        self.filename = filename
        super().__init__(
            'Unable to unpack support package {filename!r}'.format(
                filename=filename
            )
        )


class NoSupportPackage(BriefcaseCommandError):
    def __init__(self, platform, python_version):
        self.platform = platform
        self.python_version = python_version
        super().__init__(
            'Unable to locate a support package for Python {python_version} on {platform}'.format(
                python_version=python_version,
                platform=platform,
            )
        )


class DependencyInstallError(BriefcaseCommandError):
    def __init__(self):
        super().__init__(
            'Unable to install dependencies. This may be because one of your '
            'dependencies is invalid, or because pip was unable to connect '
            'to the PyPI server.'
        )


class MissingAppSources(BriefcaseCommandError):
    def __init__(self, src):
        self.src = src
        super().__init__(
            'Application source {src!r} does not exist.'.format(src=src)
        )


def cookiecutter_cache_path(template):
    """
    Determine the cookiecutter template cache directory given a template URL.

    This will return a valid path, regardless of whether `template`

    :param template: The template to use. This can be a filesystem path or
        a URL.
    :returns: The path that cookiecutter would use for the given template name.
    """
    template = template.rstrip('/')
    tail = template.split('/')[-1]
    cache_name = tail.rsplit('.git')[0]
    return Path.home() / '.cookiecutters' / cache_name


def write_dist_info(app: BaseConfig, dist_info_path: Path):
    """
    Install the dist-info folder for the application.

    :param app: The config object for the app
    :param path: The path into which the dist-info folder should be written.
    """
    # Create dist-info folder, and write a minimal metadata collection.
    dist_info_path.mkdir(exist_ok=True)
    with (dist_info_path / 'INSTALLER').open('w') as f:
        f.write('briefcase\n')
    with (dist_info_path / 'METADATA').open('w') as f:
        f.write('Metadata-Version: 2.1\n')
        f.write('Briefcase-Version: {}\n'.format(briefcase.__version__))
        f.write('Name: {app.app_name}\n'.format(app=app))
        f.write('Formal-Name: {app.formal_name}\n'.format(app=app))
        f.write('App-ID: {app.bundle}.{app.app_name}\n'.format(app=app))
        f.write('Version: {app.version}\n'.format(app=app))
        if app.url:
            f.write('Home-page: {app.url}\n'.format(app=app))
        if app.author:
            f.write('Author: {app.author}\n'.format(app=app))
        if app.author_email:
            f.write('Author-email: {app.author_email}\n'.format(app=app))
        f.write('Summary: {app.description}\n'.format(app=app))


class CreateCommand(BaseCommand):
    command = 'create'

    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        self._s3 = None

    @property
    def app_template_url(self):
        "The URL for a cookiecutter repository to use when creating apps"
        return 'https://github.com/beeware/briefcase-{self.platform}-{self.output_format}-template.git'.format(
            self=self
        )

    @property
    def support_package_url_query(self):
        """
        The query arguments to use in a support package query request.
        """
        return [
            ('platform', self.platform),
            ('version', self.python_version_tag),
        ]

    @property
    def support_package_url(self):
        "The URL of the support package to use for apps of this type."
        return "https://briefcase-support.org/python?{query}".format(
            query=urlencode(self.support_package_url_query)
        )

    def icon_targets(self, app: BaseConfig):
        """
        Obtain the dictionary of icon targets that the template requires.

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
            icon_targets = path_index['icon']
            # Convert string-specified icons into an "unknown size" icon form
            if isinstance(icon_targets, str):
                icon_targets = {
                    None: icon_targets
                }
        except KeyError:
            icon_targets = {}

        return icon_targets

    def splash_image_targets(self, app: BaseConfig):
        """
        Obtain the dictionary of splash image targets that the template requires.

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
            splash_targets = path_index['splash']
            # Convert string-specified splash images into an "unknown size" icon form
            if isinstance(splash_targets, str):
                splash_targets = {
                    None: splash_targets
                }
        except KeyError:
            splash_targets = {}

        return splash_targets

    def document_type_icon_targets(self, app: BaseConfig):
        """
        Obtain the dictionary of document type icon targets that the template requires.

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
            document_type_icon_targets = {}
            for extension, targets in path_index['document_type_icon'].items():
                # Convert string-specified icons into an "unknown size" icon form
                if isinstance(targets, str):
                    document_type_icon_targets[extension] = {
                        None: targets
                    }
                else:
                    document_type_icon_targets[extension] = targets

            return document_type_icon_targets
        except KeyError:
            return {}

    def output_format_template_context(self, app: BaseConfig):
        """
        Additional template context required by the output format.

        :param app: The config object for the app
        """
        return {}

    def generate_app_template(self, app: BaseConfig):
        """
        Create an application bundle.

        :param app: The config object for the app
        """
        # If the app config doesn't explicitly define a template,
        # use a default template.
        if app.template is None:
            app.template = self.app_template_url
        if app.template_branch is None:
            app.template_branch = self.python_version_tag

        print("Using app template: {app_template}, branch {template_branch}".format(
            app_template=app.template,
            template_branch=app.template_branch,
        ))

        # Make sure we have an updated cookiecutter template,
        # checked out to the right branch
        cached_template = self.update_cookiecutter_cache(
            template=app.template,
            branch=app.template_branch
        )

        # Construct a template context from the app configuration.
        extra_context = app.__dict__.copy()
        # Augment with some extra fields.
        extra_context.update({
            # Transformations of explicit properties into useful forms
            'module_name': app.module_name,
            'package_name': app.package_name,

            # Properties that are a function of the execution
            'year': date.today().strftime('%Y'),
            'month': date.today().strftime('%B'),
        })

        # Add in any extra template context required by the output format.
        extra_context.update(self.output_format_template_context(app))

        try:
            # Create the platform directory (if it doesn't already exist)
            output_path = self.bundle_path(app).parent
            output_path.mkdir(parents=True, exist_ok=True)
            # Unroll the template
            self.cookiecutter(
                str(cached_template),
                no_input=True,
                output_dir=os.fsdecode(output_path),
                checkout=app.template_branch,
                extra_context=extra_context
            )
        except subprocess.CalledProcessError:
            # Computer is offline
            # status code == 128 - certificate validation error.
            raise NetworkFailure("clone template repository")
        except cookiecutter_exceptions.RepositoryNotFound:
            # Either the template path is invalid,
            # or it isn't a cookiecutter template (i.e., no cookiecutter.json)
            raise InvalidTemplateRepository(app.template)
        except cookiecutter_exceptions.RepositoryCloneFailed:
            # Branch does not exist for python version
            raise TemplateUnsupportedVersion(app.template_branch)

    def install_app_support_package(self, app: BaseConfig):
        """
        Install the application support package.

        :param app: The config object for the app
        """
        try:
            # Work out if the app defines a custom override for
            # the support package URL.
            try:
                support_package_url = app.support_package
                print("Using custom support package {support_package_url}".format(
                    support_package_url=support_package_url
                ))
            except AttributeError:
                support_package_url = self.support_package_url
                print("Using support package {support_package_url}".format(
                    support_package_url=support_package_url
                ))

            if support_package_url.startswith('https://') or support_package_url.startswith('http://'):
                try:
                    print("... pinned to revision {app.support_revision}".format(
                        app=app
                    ))
                    # If a revision has been specified, add the revision
                    # as an query argument in the support package URL.
                    # This is a lot more painful than "add arg to query" should
                    # be because (a) url splits aren't appendable, and
                    # (b) Python 3.5 doesn't guarantee dictionary order.
                    url_parts = list(urlsplit(support_package_url))
                    query = []
                    for key, value in parse_qsl(url_parts[3]):
                        query.append((key, value))
                    query.append(('revision', app.support_revision))
                    url_parts[3] = urlencode(query)
                    support_package_url = urlunsplit(url_parts)

                except AttributeError:
                    # No support revision specified.
                    print("... using most recent revision")

                # Download the support file, caching the result
                # in the user's briefcase support cache directory.
                support_filename = self.download_url(
                    url=support_package_url,
                    download_path=self.dot_briefcase_path / 'support'
                )
            else:
                support_filename = Path(support_package_url)
        except requests_exceptions.ConnectionError:
            raise NetworkFailure('downloading support package')

        try:
            print("Unpacking support package...")
            support_path = self.support_path(app)
            support_path.mkdir(parents=True, exist_ok=True)
            # TODO: Py3.6 compatibility; os.fsdecode not required in Py3.7
            self.shutil.unpack_archive(
                os.fsdecode(support_filename),
                extract_dir=os.fsdecode(support_path)
            )
        except (shutil.ReadError, EOFError):
            print()
            raise InvalidSupportPackage(support_package_url)

    def install_app_dependencies(self, app: BaseConfig):
        """
        Install the dependencies for the app.

        :param app: The config object for the app
        """

        target = self.app_packages_path(app)

        # Clear existing dependency directory
        if target.is_dir():
            self.shutil.rmtree(target)
            self.os.mkdir(target)

        # Install  dependencies
        if app.requires:
            try:
                self.subprocess.run(
                    [
                        sys.executable, "-m",
                        "pip", "install",
                        "--upgrade",
                        "--no-user",
                        "--target={}".format(target),
                    ] + app.requires,
                    check=True,
                )
            except subprocess.CalledProcessError:
                raise DependencyInstallError()
        else:
            print("No application dependencies.")

    def install_app_code(self, app: BaseConfig):
        """
        Install the application code into the bundle.

        :param app: The config object for the app
        """
        if app.sources:
            for src in app.sources:
                print("Installing {src}...".format(src=src))
                original = self.base_path / src
                target = self.app_path(app) / original.name

                # Remove existing versions of the code
                if target.exists():
                    if target.is_dir():
                        self.shutil.rmtree(target)
                    else:
                        target.unlink()

                # Install the new copy of the app code.
                if not original.exists():
                    raise MissingAppSources(src)
                elif original.is_dir():
                    self.shutil.copytree(original, target)
                else:
                    self.shutil.copy(original, target)
        else:
            print("No sources defined for {app.app_name}.".format(app=app))

        # Write the dist-info folder for the application.
        write_dist_info(
            app=app,
            dist_info_path=self.app_path(app) / '{app.module_name}-{app.version}.dist-info'.format(
                app=app,
            )
        )

    def install_image(self, role, variant, size, source, target):
        """
        Install an icon/image of the requested size at a target location, using
        the source images defined by the app config.

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
                    source_filename = '{source}{target.suffix}'.format(
                        source=source,
                        target=target,
                    )
                    full_role = role
                else:
                    try:
                        source_filename = '{source}{target.suffix}'.format(
                            source=source[variant],
                            target=target,
                        )
                        full_role = '{variant} {role}'.format(
                            variant=variant,
                            role=role,
                        )
                    except (TypeError, KeyError):
                        print(
                            "Unable to find {variant} variant for {role}; "
                            "using default".format(
                                variant=variant,
                                role=role,
                            )
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
                        source_filename = '{source}{target.suffix}'.format(
                            source=source[size],
                            target=target,
                        )
                        full_role = '{size} {role}'.format(
                            size=size,
                            role=role,
                        )
                    except TypeError:
                        # The lookup on the source failed; that means we
                        # have an sized image without variants.
                        source_filename = '{source}-{size}{target.suffix}'.format(
                            source=source,
                            size=size,
                            target=target,
                        )
                        full_role = '{size}px {role}'.format(
                            size=size,
                            role=role,
                        )

                else:
                    try:
                        source_filename = '{source}-{size}{target.suffix}'.format(
                            source=source[variant],
                            size=size,
                            target=target,
                        )
                        full_role = '{size}px {variant} {role}'.format(
                            size=size,
                            variant=variant,
                            role=role,
                        )
                    except (TypeError, KeyError):
                        print(
                            "Unable to find {size}px {variant} variant for {role}; "
                            "using default".format(
                                size=size,
                                variant=variant,
                                role=role,
                            )
                        )
                        return

            full_source = self.base_path / source_filename
            if full_source.exists():
                print("Installing {source_filename} as {full_role}...".format(
                    source_filename=source_filename,
                    full_role=full_role,
                ))

                # Make sure the target directory exists
                target.parent.mkdir(parents=True, exist_ok=True)
                # Copy the source image to the target location
                self.shutil.copy(full_source, target)
            else:
                print(
                    "Unable to find {source_filename} for {full_role}; using default".format(
                        full_role=full_role,
                        source_filename=source_filename,
                    )
                )

    def install_app_resources(self, app: BaseConfig):
        """
        Install the application resources (such as icons and splash screens) into
        the bundle.

        :param app: The config object for the app
        """
        for variant_or_size, targets in self.icon_targets(app).items():
            try:
                # Treat the targets as a dictionary of sizes;
                # if there's no `items`, then it's an icon without variants.
                for size, target in targets.items():
                    self.install_image(
                        'application icon',
                        source=app.icon,
                        variant=variant_or_size,
                        size=size,
                        target=self.bundle_path(app) / target
                    )
            except AttributeError:
                # Either a single variant, or a single size.
                self.install_image(
                    'application icon',
                    source=app.icon,
                    variant=None,
                    size=variant_or_size,
                    target=self.bundle_path(app) / targets
                )

        for variant_or_size, targets in self.splash_image_targets(app).items():
            try:
                # Treat the targets as a dictionary of sizes;
                # if there's no `items`, then it's a splash without variants
                for size, target in targets.items():
                    self.install_image(
                        'splash image',
                        source=app.splash,
                        variant=variant_or_size,
                        size=size,
                        target=self.bundle_path(app) / target
                    )
            except AttributeError:
                # Either a single variant, or a single size.
                self.install_image(
                    'splash image',
                    source=app.splash,
                    variant=None,
                    size=variant_or_size,
                    target=self.bundle_path(app) / targets
                )

        for extension, doctype in self.document_type_icon_targets(app).items():
            for size, target in doctype.items():
                self.install_image(
                    'icon for .{extension} documents'.format(extension=extension),
                    size=size,
                    source=app.document_types[extension]['icon'],
                    variant=None,
                    target=self.bundle_path(app) / target,
                )

    def create_app(self, app: BaseConfig, **options):
        """
        Create an application bundle.

        :param app: The config object for the app
        """
        if not app.supported:
            raise UnsupportedPlatform(self.platform)

        bundle_path = self.bundle_path(app)
        if bundle_path.exists():
            print()
            confirm = self.input.boolean_input(
                'Application {app.app_name} already exists; overwrite'.format(app=app),
                default=False
            )
            if not confirm:
                print("Aborting creation of app {app.app_name}".format(
                    app=app
                ))
                return
            print()
            print("[{app.app_name}] Removing old application bundle...".format(
                app=app
            ))
            self.shutil.rmtree(bundle_path)

        print()
        print('[{app.app_name}] Generating application template...'.format(
            app=app
        ))
        self.generate_app_template(app=app)

        print()
        print('[{app.app_name}] Installing support package...'.format(
            app=app
        ))
        self.install_app_support_package(app=app)

        print()
        print('[{app.app_name}] Installing dependencies...'.format(
            app=app
        ))
        self.install_app_dependencies(app=app)

        print()
        print('[{app.app_name}] Installing application code...'.format(
            app=app
        ))
        self.install_app_code(app=app)

        print()
        print('[{app.app_name}] Installing application resources...'.format(
            app=app
        ))
        self.install_app_resources(app=app)
        print()

        print("[{app.app_name}] Created {filename}".format(
            app=app,
            filename=self.bundle_path(app).relative_to(self.base_path),
        ))

    def verify_tools(self):
        """
        Verify that the tools needed to run this command exist

        Raises MissingToolException if a required system tool is missing.
        """
        self.git = self.integrations.git.verify_git_is_installed(self)

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
