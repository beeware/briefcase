
import argparse
from cgi import parse_header
import importlib
import inspect
import os
import platform
import shutil
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse

import requests
from cookiecutter.main import cookiecutter
from cookiecutter.repository import is_repo_url

from briefcase import __version__
from briefcase.config import AppConfig, GlobalConfig, parse_config
from briefcase.exceptions import (
    BadNetworkResourceError,
    BriefcaseCommandError,
    BriefcaseConfigError,
    MissingNetworkResourceError
)

try:
    import git
except ImportError:
    # If git isn't installed, importing `git` will fail. Catch the error
    # and replace the git module with a dummy; raise an error when tools
    # are verified.
    git = None


class TemplateUnsupportedVersion(BriefcaseCommandError):
    def __init__(self, version_tag):
        self.version_tag = version_tag
        super().__init__(
            msg='Template does not support {version_tag}'.format(
                version_tag=version_tag
            )
        )


def create_config(klass, config, msg):
    try:
        return klass(**config)
    except TypeError:
        # Inspect the GlobalConfig constructor to find which
        # parameters are required and don't have a default
        # value.
        required_args = {
            name
            for name, param in inspect.signature(klass.__init__).parameters.items()
            if param.default == inspect._empty
            and name not in {'self', 'kwargs'}
        }
        missing_args = required_args - config.keys()
        missing = ', '.join(
            "'{arg}'".format(arg=arg)
            for arg in sorted(missing_args)
        )
        raise BriefcaseConfigError(
            "{msg} is incomplete (missing {missing})".format(
                msg=msg,
                missing=missing
            )
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


def full_kwargs(state, kwargs):
    """
    Merge command state with keyword arguments.

    Command state takes precedence over any keyword argument.

    :param state: The current command state. Can be ``None``.
    :param kwargs: The base keyword arguments.
    :returns: A dictionary containing all of ``kwargs``, with any values
        provided in ``state`` overriding the base ``kwargs`` values.
    """
    if state is not None:
        full = kwargs.copy()
        full.update(state)
    else:
        full = kwargs

    return full


class BaseCommand(ABC):
    cmd_line = "briefcase {command} {platform} {output_format}"
    GLOBAL_CONFIG_CLASS = GlobalConfig
    APP_CONFIG_CLASS = AppConfig

    def __init__(
            self,
            base_path,
            dot_briefcase_path=Path.home() / ".briefcase",
            apps=None,
            ):
        self.base_path = base_path
        self.dot_briefcase_path = dot_briefcase_path

        self.global_config = None
        self.apps = {} if apps is None else apps

        # Some details about the host machine
        self.host_arch = platform.machine()
        self.host_os = platform.system()

        # External service APIs.
        # These are abstracted to enable testing without patching.
        self.cookiecutter = cookiecutter
        self.git = git
        self.requests = requests
        self.input = input
        self.os = os
        self.shutil = shutil
        self.subprocess = subprocess

    @property
    def create_command(self):
        "Factory property; return an instance of a create command for the same format"
        format_module = importlib.import_module(self.__module__)
        return format_module.create(base_path=self.base_path, apps=self.apps)

    @property
    def update_command(self):
        "Factory property; return an instance of an update command for the same format"
        format_module = importlib.import_module(self.__module__)
        return format_module.update(base_path=self.base_path, apps=self.apps)

    @property
    def build_command(self):
        "Factory property; return an instance of a build command for the same format"
        format_module = importlib.import_module(self.__module__)
        return format_module.build(base_path=self.base_path, apps=self.apps)

    @property
    def run_command(self):
        "Factory property; return an instance of a run command for the same format"
        format_module = importlib.import_module(self.__module__)
        return format_module.run(base_path=self.base_path, apps=self.apps)

    @property
    def package_command(self):
        "Factory property; return an instance of a package command for the same format"
        format_module = importlib.import_module(self.__module__)
        return format_module.package(base_path=self.base_path, apps=self.apps)

    @property
    def publish_command(self):
        "Factory property; return an instance of a publish command for the same format"
        format_module = importlib.import_module(self.__module__)
        return format_module.publish(base_path=self.base_path, apps=self.apps)

    @property
    def platform_path(self):
        """
        The path for all applications for this command's platform
        """
        return self.base_path / self.platform

    def bundle_path(self, app):
        """
        The path to the bundle for the app in the output format.

        The bundle is the template-generated source form of the app.
        The path will usually be a directory, the existence of which is
        indicative that the template has been rolled out for an app.

        :param app: The app config
        """
        return self.platform_path / app.formal_name

    @abstractmethod
    def binary_path(self, app):
        """
        The path to the executable artefact for the app in the output format.

        This may be a binary file produced by compilation; however, if
        the output format doesn't require compilation, it may be the same
        as the bundle path (assuming the bundle path is inherently
        "executable"), or a path that reasonably represents the thing that can
        be executed.

        :param app: The app config
        """
        ...

    @abstractmethod
    def distribution_path(self, app):
        """
        The path to the distributable artefact for the app in the output format.

        This is the single file that should be uploaded for distribution.
        This may be the binary (if the binary is a self contained executable);
        however, if the output format produces an installer, it will be the
        path to the installer.

        :param app: The app config
        """
        ...

    def app_module_path(self, app):
        """
        Find the path for the application module for an app.

        :param app: The config object for the app
        :returns: The Path to the dist-info folder.
        """
        app_home = [
            path.split('/')
            for path in app.sources
            if path.rsplit('/', 1)[-1] == app.module_name
        ]
        try:
            if len(app_home) == 1:
                path = Path(str(self.base_path), *app_home[0])
            else:
                raise BriefcaseCommandError(
                    "Multiple paths in sources found for application '{app.app_name}'".format(app=app)
                )
        except IndexError:
            raise BriefcaseCommandError(
                "Unable to find code for application '{app.app_name}'".format(app=app)
            )

        return path

    @property
    def python_version_tag(self):
        """
        The major.minor of the Python version in use, as a string.

        This is used as a repository label/tag to identify the appropriate
        templates, etc to use.
        """
        return '{major}.{minor}'.format(
            major=sys.version_info.major,
            minor=sys.version_info.minor
        )

    def verify_tools(self):
        """
        Verify that the tools needed to run this command exist

        Raises MissingToolException if a required system tool is missing.
        """
        # Check whether the git executable could be imported.
        if self.git is None:
            raise BriefcaseCommandError("""
Briefcase requires git, but it is not installed (or is not on your PATH). Visit:

    https://git-scm.com/

to download and install git. If you have installed git recently and are still
getting this error, you may need to restart your terminal session.
""")

    def parse_options(self, extra):
        parser = argparse.ArgumentParser(
            prog=self.cmd_line.format(
                command=self.command,
                platform=self.platform,
                output_format=self.output_format
            ),
            description=self.description,
        )

        self.add_default_options(parser)
        self.add_options(parser)

        # Parse the full set of command line options from the content
        # remaining after the basic command/platform/output format
        # has been extracted.
        return vars(parser.parse_args(extra))

    def add_default_options(self, parser):
        """
        Add the default options that exist on *all* commands

        :param parser: a stub argparse parser for the command.
        """
        parser.add_argument(
            '-v', '--verbosity',
            action='count',
            default=1,
            help="set the verbosity of output"
        )
        parser.add_argument(
            '-V', '--version',
            action='version',
            version=__version__
        )

    def add_options(self, parser):
        """
        Add any options that this command needs to parse from the command line.

        :param parser: a stub argparse parser for the command.
        """
        pass

    def parse_config(self, filename):
        try:
            with open(filename) as config_file:
                # Parse the content of the pyproject.toml file, extracting
                # any platform and output format configuration for each app,
                # creating a single set of configuration options.
                global_config, app_configs = parse_config(
                    config_file,
                    platform=self.platform,
                    output_format=self.output_format
                )

                self.global_config = create_config(
                    klass=self.GLOBAL_CONFIG_CLASS,
                    config=global_config,
                    msg="Global configuration"
                )

                for app_name, app_config in app_configs.items():
                    # Construct an AppConfig object with the final set of
                    # configuration options for the app.
                    self.apps[app_name] = create_config(
                        klass=self.APP_CONFIG_CLASS,
                        config=app_config,
                        msg="Configuration for '{app_name}'".format(
                            app_name=app_name
                        )
                    )

        except FileNotFoundError:
            raise BriefcaseConfigError('configuration file not found')

    def download_url(self, url, download_path):
        """
        Download a given URL, caching it. If it has already been downloaded,
        return the value that has been cached.

        This is a utility method used to obtain assets used by the
        install process. The cached filename will be the filename portion of
        the URL, appended to the download path.

        :param url: The URL to download
        :param download_path: The path to the download cache folder. This path
            will be created if it doesn't exist.
        :returns: The filename of the downloaded (or cached) file.
        """
        download_path.mkdir(parents=True, exist_ok=True)

        response = self.requests.get(url, stream=True)
        if response.status_code == 404:
            raise MissingNetworkResourceError(
                url=url,
            )
        elif response.status_code != 200:
            raise BadNetworkResourceError(
                url=url,
                status_code=response.status_code
            )

        # The initial URL might (read: will) go through URL redirects, so
        # we need the *final* response. We look at either the `Content-Disposition`
        # header, or the final URL, to extract the cache filename.
        cache_full_name = urlparse(response.url).path
        header_value = response.headers.get('Content-Disposition')
        if header_value:
            # See also https://tools.ietf.org/html/rfc6266
            value, parameters = parse_header(header_value)
            if (value.split(':', 1)[-1].strip().lower() == 'attachment' and parameters.get('filename')):
                cache_full_name = parameters['filename']
        cache_name = cache_full_name.split('/')[-1]
        filename = download_path / cache_name
        if not filename.exists():
            # We have meaningful content, and it hasn't been cached previously,
            # so save it in the requested location
            print('Downloading {cache_name}...'.format(cache_name=cache_name))
            with filename.open('wb') as f:
                total = response.headers.get('content-length')
                if total is None:
                    f.write(response.content)
                else:
                    downloaded = 0
                    total = int(total)
                    for data in response.iter_content(chunk_size=1024 * 1024):
                        downloaded += len(data)
                        f.write(data)
                        done = int(50 * downloaded / total)
                        print('\r{}{} {}%'.format('#' * done, '.' * (50-done), 2*done), end='', flush=True)
            print()
        else:
            print('{cache_name} already downloaded'.format(cache_name=cache_name))
        return filename

    def update_cookiecutter_cache(self, template: str, branch='master'):
        """
        Ensure that we have a current checkout of a template path.

        If the path is a local path, use the path as is.

        If the path is a URL, look for a local cache; if one exists, update it,
        including checking out the required branch.

        :param template: The template URL or path.
        :param branch: The template branch to use. Default: ``master``
        :return: The path to the cached template. This may be the originally
            provided path if the template was a file path.
        """
        if is_repo_url(template):
            # The app template is a repository URL.
            #
            # When in `no_input=True` mode, cookiecutter deletes and reclones
            # a template directory, rather than updating the existing repo.
            #
            # Look for a cookiecutter cache of the template; if one exists,
            # try to update it using git. If no cache exists, or if the cache
            # directory isn't a git directory, or git fails for some reason,
            # fall back to using the specified template directly.
            try:
                cached_template = cookiecutter_cache_path(template)
                repo = self.git.Repo(cached_template)
                try:
                    # Attempt to update the repository
                    remote = repo.remote(name='origin')
                    remote.fetch()
                except git.exc.GitCommandError:
                    # We are offline, or otherwise unable to contact
                    # the origin git repo. It's OK to continue; but warn
                    # the user that the template may be stale.
                    print("***************************************************************************")
                    print("WARNING: Unable to update template (is your computer offline?)")
                    print("WARNING: Briefcase will use existing template without updating.")
                    print("***************************************************************************")
                try:
                    # Check out the branch for the required version tag.
                    head = remote.refs[branch]

                    print("Using existing template (sha {hexsha}, updated {datestamp})".format(
                        hexsha=head.commit.hexsha,
                        datestamp=head.commit.committed_datetime.strftime("%c")
                    ))
                    head.checkout()
                except IndexError:
                    # No branch exists for the requested version.
                    raise TemplateUnsupportedVersion(branch)
            except git.exc.NoSuchPathError:
                # Template cache path doesn't exist.
                # Just use the template directly, rather than attempting an update.
                cached_template = template
            except git.exc.InvalidGitRepositoryError:
                # Template cache path exists, but isn't a git repository
                # Just use the template directly, rather than attempting an update.
                cached_template = template
        else:
            # If this isn't a repository URL, treat it as a local directory
            cached_template = template

        return cached_template
