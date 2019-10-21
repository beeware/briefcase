import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import boto3
import toml
from botocore.handlers import disable_signing
from git import exc as git_exceptions
from cookiecutter import exceptions as cookiecutter_exceptions
from requests import exceptions as requests_exceptions

from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError, NetworkFailure

from .base import BaseCommand


class TemplateUnsupportedPythonVersion(BriefcaseCommandError):
    def __init__(self, version_tag):
        self.version_tag = version_tag
        super().__init__(
            msg='Template does not support Python version {version_tag}'.format(
                version_tag=version_tag
            )
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


class CreateCommand(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._path_index = {}
        self._s3 = None
        self._support_package_url = None

    @property
    def template_url(self):
        "The URL for a cookiecutter repository to use when creating apps"
        return 'https://github.com/beeware/briefcase-{self.platform}-{self.output_format}-template.git'.format(
            self=self
        )

    def _anonymous_s3_client(self, region):
        """
        Set up an anonymous S3 client.

        :param region: The AWS region name
        :return: An S3 boto client, with request signing disabled.
        """
        if self._s3 is None:
            self._s3 = boto3.client('s3', region_name=region)
            self._s3.meta.events.register('choose-signer.s3.*', disable_signing)

        return self._s3

    @property
    def support_package_url(self):
        "The URL of the support package to use for apps of this type."
        if self._support_package_url is None:
            # Get an S3 client, and disable signing (so we don't need credentials)
            S3_BUCKET = 'briefcase-support'
            S3_REGION = 'us-west-2'
            S3_URL = 'https://{}.s3-{}.amazonaws.com/'.format(S3_BUCKET, S3_REGION)

            s3 = self._anonymous_s3_client(region=S3_REGION)

            top_build_number = 0
            top_build = None
            paginator = s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(
                Bucket=S3_BUCKET,
                Prefix='python/{}/{}/'.format(
                    self.python_version_tag,
                    self.platform
                )
            ):
                for item in page.get('Contents', []):
                    build_number = int(
                        item['Key'].rstrip('.tar.gz').split('.')[-1].lstrip('b')
                    )
                    if build_number > top_build_number:
                        top_build_number = build_number
                        top_build = item['Key']

            if top_build is None:
                raise NoSupportPackage(
                    platform=self.platform,
                    python_version=self.python_version_tag
                )
            self._support_package_url = S3_URL + top_build

        return self._support_package_url

    def _load_path_index(self, app: BaseConfig):
        "Load the path index from the index file provided by the app template"
        with open(self.bundle_path(app) / 'briefcase.toml') as f:
            self._path_index[app] = toml.load(f)['paths']
        return self._path_index[app]

    def support_path(self, app: BaseConfig):
        "The path into which the support package should be unpacked"
        # If the index file hasn't been loaded for this app, load it.
        try:
            path_index = self._path_index[app]
        except KeyError:
            path_index = self._load_path_index(app)
        return self.bundle_path(app) / path_index['support_path']

    def app_packages_path(self, app: BaseConfig):
        "The path into which dependencies should be installed"
        # If the index file hasn't been loaded for this app, load it.
        try:
            path_index = self._path_index[app]
        except KeyError:
            path_index = self._load_path_index(app)
        return self.bundle_path(app) / path_index['app_packages_path']

    def app_path(self, app: BaseConfig):
        "The path into which the application should be installed"
        # If the index file hasn't been loaded for this app, load it.
        try:
            path_index = self._path_index[app]
        except KeyError:
            path_index = self._load_path_index(app)
        return self.bundle_path(app) / path_index['app_path']

    def generate_app_template(self, app: BaseConfig):
        """
        Create an application bundle.

        :param app: The config object for the app
        """
        # If the app config doesn't explicitly define a template,
        # use a default template.
        if app.template is None:
            app.template = self.template_url

        print("Using app template: {app_template}".format(
            app_template=app.template,
        ))

        # When in `no_input=True` mode, cookiecutter deletes and reclones
        # a template directory, rather than updating the existing repo.

        # Look for a cookiecutter cache of the template; if one exists,
        # try to update it using git. If no cache exists, or if the cache
        # directory isn't a git directory, or git fails for some reason,
        # fall back to using the specified template directly.
        try:
            template = cookiecutter_cache_path(app.template)
            repo = self.git.Repo(template)
            try:
                # Attempt to update the repository
                remote = repo.remote(name='origin')
                remote.fetch()
            except git_exceptions.GitCommandError:
                # We are offline, or otherwise unable to contact
                # the origin git repo. It's OK to continue; but warn
                # the user that the template may be stale.
                print("***************************************************************************")
                print("WARNING: Unable to update application template (is your computer offline?)")
                print("WARNING: Briefcase will use existing template without updating.")
                print("***************************************************************************")
            try:
                # Check out the branch for the required version tag.
                head = repo.create_head(self.python_version_tag, remote.refs[self.python_version_tag])
                print("Using existing template (sha {hexsha}, updated {datestamp})".format(
                    hexsha=head.commit.hexsha,
                    datestamp=head.commit.committed_datetime.strftime("%c")
                ))
                head.checkout()
            except IndexError:
                # No branch exists for the requested version.
                raise TemplateUnsupportedPythonVersion(self.python_version_tag)
        except git_exceptions.NoSuchPathError:
            # Template cache path doesn't exist.
            # Just use the template directly, rather than attempting an update.
            template = app.template
        except git_exceptions.InvalidGitRepositoryError:
            # Template cache path exists, but isn't a git repository
            # Just use the template directly, rather than attempting an update.
            template = app.template

        # Construct a template context from the app configuration.
        extra_context = app.__dict__.copy()
        # Augment with some extra fields.
        extra_context.update({
            # Transformations of explicit properties into useful forms
            'module_name': app.module_name,
            'class_name': app.class_name,

            # Properties that are a function of the execution
            'year': date.today().strftime('%Y'),
            'month': date.today().strftime('%B'),
        })

        try:
            # Create the platform directory (if it doesn't already exist)
            self.platform_path.mkdir(parents=True, exist_ok=True)
            # Unroll the template
            self.cookiecutter(
                str(template),
                no_input=True,
                output_dir=str(self.platform_path),
                checkout=self.python_version_tag,
                extra_context=extra_context
            )
        except subprocess.CalledProcessError:
            # Computer is offline
            raise NetworkFailure("clone template repository")
        except cookiecutter_exceptions.RepositoryNotFound:
            # Either the template path is invalid,
            # or it isn't a cookiecutter template (i.e., no cookiecutter.json)
            raise InvalidTemplateRepository(app.template)
        except cookiecutter_exceptions.RepositoryCloneFailed:
            # Branch does not exist for python version
            raise TemplateUnsupportedPythonVersion(self.python_version_tag)

    def install_app_support_package(self, app: BaseConfig):
        """
        Install the application support packge.

        :param app: The config object for the app
        """
        try:
            # Work out if the app defines a custom override for
            # the support package URL.
            try:
                support_package_url = app.support_package_url
                print("Using custom support package {support_package_url}".format(
                    support_package_url=support_package_url
                ))
            except AttributeError:
                support_package_url = self.support_package_url
                print("Using support package {support_package_url}".format(
                    support_package_url=support_package_url
                ))

            # Download the support file, caching the result
            # in the user's briefcase support cache directory.
            support_filename = self.download_url(
                url=support_package_url,
                download_path=Path.home() / '.briefcase' / 'support'
            )
        except requests_exceptions.ConnectionError:
            raise NetworkFailure('downloading support package')

        try:
            print("Unpacking support package...")
            support_path = self.support_path(app)
            support_path.mkdir(parents=True, exist_ok=True)
            self.shutil.unpack_archive(
                str(support_filename),
                extract_dir=str(support_path)
            )
        except shutil.ReadError:
            raise InvalidSupportPackage(support_filename.name)

    def install_app_dependencies(self, app: BaseConfig):
        """
        Install the dependencies for the app.

        :param app: The config object for the app
        """
        if app.requires:
            try:
                self.subprocess.run(
                    [
                        sys.executable, "-m",
                        "pip", "install",
                        "--upgrade",
                        '--target={}'.format(self.app_packages_path(app)),
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
            print("No sources defined for {app.name}.".format(app=app))

        # Create dist-info folder, and write a minimal metadata collection.
        dist_info_path = self.app_path(app) / '{app.module_name}-{app.version}.dist-info'.format(
            app=app,
        )
        dist_info_path.mkdir(exist_ok=True)
        with open(dist_info_path / 'INSTALLER', 'w') as f:
            f.write('briefcase\n')
        with open(dist_info_path / 'METADATA', 'w') as f:
            f.write('Metadata-Version: 2.1\n')
            f.write('Name: {app.name}\n'.format(app=app))
            f.write('Formal-Name: {app.formal_name}\n'.format(app=app))
            f.write('Bundle: {app.bundle}\n'.format(app=app))
            f.write('Version: {app.version}\n'.format(app=app))
            # f.write('License: {}\n'.format(app=app))
            # f.write('Home-page: {}\n'.format(app=app))
            # f.write('Author: {}\n'.format(app=app))
            # f.write('Author-email: {}\n'.format(app=app))
            # f.write('Maintainer: {}\n'.format(app=app))
            # f.write('Maintainer-email:  {}\n'.format(app=app))
            f.write('Summary: {app.description}\n'.format(app=app))

    def install_app_extras(self, app: BaseConfig):
        """
        Install the application extras (such as icons and splash screens) into
        the bundle.

        :param app: The config object for the app
        :param bundle_path: The path where the application bundle should be created.
        """
        # if app.icon:
        #     self.install_icon(app)
        # else:
        #     print("No icon defined for {app.name}; using default".format(app=app))

    # def install_icon(self):
    #     shutil.copyfile(
    #         "%s.icns" % self.icon,
    #         os.path.join(self.resource_dir, '%s.icns' % self.distribution.get_name())
    #     )

    #     for tag, doctype in self.document_types.items():
    #         shutil.copyfile(
    #             "%s.icns" % doctype['icon'],
    #             os.path.join(self.resource_dir, "%s-%s.icns" %
    #                          (self.distribution.get_name(), tag))
    #         )

    def create_app(self, app: BaseConfig):
        """
        Create an application bundle.

        :param app: The config object for the app
        """
        bundle_path = self.bundle_path(app)
        if bundle_path.exists():
            print()
            confirm = self.input('Application {app.name} already exists; overwrite (y/N)? '.format(
                app=app
            ))
            if confirm.lower() != 'y':
                print("Aborting creation of app {app.name}".format(
                    app=app
                ))
                return
            print()
            print("[{app.name}] Removing old application bundle...".format(
                app=app
            ))
            shutil.rmtree(bundle_path)
        print()
        print('[{app.name}] Generate application template...'.format(
            app=app
        ))
        self.generate_app_template(app=app)

        print()
        print('[{app.name}] Install support package...'.format(
            app=app
        ))
        self.install_app_support_package(app=app)

        print()
        print('[{app.name}] Install dependencies...'.format(
            app=app
        ))
        self.install_app_dependencies(app=app)

        print()
        print('[{app.name}] Install application code...'.format(
            app=app
        ))
        self.install_app_code(app=app)

        print()
        print('[{app_name}] Install extra application resources...'.format(
            app_name=app.name
        ))
        self.install_app_extras(app=app)

    def __call__(self, app: Optional[BaseConfig] = None):
        self.verify_tools()

        if app:
            self.create_app(app)
        else:
            for app_name, app in self.apps.items():
                self.create_app(app)
