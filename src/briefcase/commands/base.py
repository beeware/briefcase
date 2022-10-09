import argparse
import importlib
import inspect
import os
import platform
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from cookiecutter import exceptions as cookiecutter_exceptions
from cookiecutter.repository import is_repo_url
from platformdirs import PlatformDirs

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from briefcase import __version__
from briefcase.config import AppConfig, BaseConfig, GlobalConfig, parse_config
from briefcase.console import Console, Log
from briefcase.exceptions import (
    BriefcaseCommandError,
    BriefcaseConfigError,
    InfoHelpText,
    NetworkFailure,
)
from briefcase.integrations.base import ToolCache


class InvalidTemplateRepository(BriefcaseCommandError):
    def __init__(self, template):
        self.template = template
        super().__init__(
            f"Unable to clone application template; is the template path {template!r} correct?"
        )


class TemplateUnsupportedVersion(BriefcaseCommandError):
    def __init__(self, briefcase_version):
        self.briefcase_version = briefcase_version
        super().__init__(
            f"Could not find a template branch for Briefcase {briefcase_version}."
        )


class UnsupportedPlatform(BriefcaseCommandError):
    def __init__(self, platform):
        self.platform = platform
        super().__init__(
            f"""\
App cannot be deployed on {platform}. This is probably because one or more
dependencies (e.g., the GUI library) doesn't support {platform}.
"""
        )


def create_config(klass, config, msg):
    try:
        return klass(**config)
    except TypeError as e:
        # Inspect the GlobalConfig constructor to find which
        # parameters are required and don't have a default value.
        required_args = {
            name
            for name, param in inspect.signature(klass.__init__).parameters.items()
            if param.default == inspect._empty and name not in {"self", "kwargs"}
        }
        missing_args = required_args - config.keys()
        missing = ", ".join(f"'{arg}'" for arg in sorted(missing_args))
        raise BriefcaseConfigError(f"{msg} is incomplete (missing {missing})") from e


def cookiecutter_cache_path(template):
    """Determine the cookiecutter template cache directory given a template
    URL.

    This will return a valid path, regardless of whether `template`

    :param template: The template to use. This can be a filesystem path or
        a URL.
    :returns: The path that cookiecutter would use for the given template name.
    """
    template = template.rstrip("/")
    tail = template.split("/")[-1]
    cache_name = tail.rsplit(".git")[0]
    return Path.home() / ".cookiecutters" / cache_name


def full_options(state, options):
    """Merge command state with keyword arguments.

    Command state takes precedence over any keyword argument.

    :param state: The current command state. Can be ``None``.
    :param options: The base options.
    :returns: A dictionary containing all of ``options``, with any values
        provided in ``state`` overriding the base ``options`` values.
    """
    if state is not None:
        full = options.copy()
        full.update(state)
    else:
        full = options

    return full


class BaseCommand(ABC):
    cmd_line = "briefcase {command} {platform} {output_format}"
    GLOBAL_CONFIG_CLASS = GlobalConfig
    APP_CONFIG_CLASS = AppConfig

    def __init__(
        self,
        logger: Log,
        console: Console,
        tools: ToolCache = None,
        apps: dict = None,
        base_path: Path = None,
        data_path: Path = None,
        is_clone: bool = False,
    ):
        """Base for all Commands.

        :param logger: Logger for console and logfile.
        :param console: Facilitates console interaction and input solicitation.
        :param tools: Cache of tools populated by Commands as they are required.
        :param apps: Dictionary of project's Apps keyed by app name.
        :param base_path: Base directory for Briefcase project.
        :param data_path: Base directory for Briefcase tools, support packages, etc.
        :param is_clone: Flag that Command was triggered by the user's requested Command;
            for instance, RunCommand can invoke UpdateCommand and/or BuildCommand.
        """
        if base_path is None:
            self.base_path = Path.cwd()
        else:
            self.base_path = base_path
        self.data_path = self.validate_data_path(data_path)
        self.apps = {} if apps is None else apps
        self.is_clone = is_clone

        self.tools = tools or ToolCache(
            logger=logger,
            console=console,
            base_path=self.data_path / "tools",
        )

        self.global_config = None
        self._path_index = {}

    @property
    def logger(self):
        return self.tools.logger

    @property
    def input(self):
        return self.tools.input

    def check_obsolete_data_dir(self):
        """Inform user if obsolete data directory exists.

        TODO: Remove this check after 1 JAN 2023 since most users will have transitioned by then

        Previous versions used the ~/.briefcase directory to store
        downloads, tools, etc. This check lets users know the old
        directory still exists and their options to migrate or clean up.
        """
        dot_briefcase_path = self.tools.home_path / ".briefcase"

        # If there's no .briefcase path, no need to check for migration.
        if not dot_briefcase_path.exists():
            return

        # If the data path is user-provided, don't check for migration.
        if "BRIEFCASE_HOME" in os.environ:
            return

        if self.data_path.exists():
            self.logger.warning(
                f"""\
Briefcase is no longer using the data directory:

    {dot_briefcase_path}

This directory can be safely deleted.
"""
            )
        else:
            self.logger.warning(
                f"""\
*************************************************************************
** NOTICE: Briefcase is changing its data directory                   **
*************************************************************************

    Briefcase is moving its data directory from:

        {dot_briefcase_path}

    to:

        {self.data_path}

    If you continue, Briefcase will re-download the tools and data it
    uses to build and package applications.

    To avoid potentially large downloads and long installations, you
    can manually move the old data directory to the new location.

    If you continue and allow Briefcase to re-download its tools, the
    old data directory can be safely deleted.

*************************************************************************
"""
            )
            self.input.prompt()
            if not self.input.boolean_input(
                "Do you want to re-download the Briefcase support tools",
                # Default to continuing for non-interactive runs
                default=not self.input.enabled,
            ):
                raise InfoHelpText(
                    f"""\
Move the Briefcase data directory from:

    {dot_briefcase_path}

to:

    {self.data_path}

or delete the old data directory, and re-run Briefcase.

"""
                )

            # Create data directory to prevent full notice showing again.
            self.data_path.mkdir(parents=True, exist_ok=True)

    def validate_data_path(self, data_path):
        """Validate provided data path or determine OS-specific path.

        If a data path is provided during construction, use it. This
        usually indicates we're under test conditions. If there's no
        data path provided, look for a BRIEFCASE_HOME environment
        variable. If that isn't defined, use a platform-specific default
        data path.
        """
        if data_path is None:
            try:
                briefcase_home = os.environ["BRIEFCASE_HOME"]
                data_path = Path(briefcase_home).resolve()
                # Path("") converts to ".", so check for that edge case.
                if briefcase_home == "" or not data_path.exists():
                    raise BriefcaseCommandError(
                        "The path specified by BRIEFCASE_HOME does not exist."
                    )
            except KeyError:
                if platform.system() == "Darwin":
                    # macOS uses a bundle name, rather than just the app name
                    app_name = "org.beeware.briefcase"
                else:
                    app_name = "briefcase"

                data_path = PlatformDirs(
                    appname=app_name,
                    appauthor="BeeWare",
                ).user_cache_path

        if " " in os.fsdecode(data_path):
            raise BriefcaseCommandError(
                f"""
The location Briefcase will use to store tools and support files:

    {data_path}

contains spaces. This will cause problems with some tools, preventing
you from building and packaging applications.

You can set the environment variable BRIEFCASE_HOME to specify
a custom location for Briefcase's tools.

"""
            )

        return Path(data_path)

    def _command_factory(self, command_name: str):
        """Command factory for the current platform and format.

        :param command_name: name of Command (e.g. 'create', 'build', 'run', etc.)
        :return: instantiated Command
        """
        format_module = importlib.import_module(self.__module__)
        command = getattr(format_module, command_name)(
            base_path=self.base_path,
            apps=self.apps,
            logger=self.logger,
            console=self.input,
            tools=self.tools,
            is_clone=True,
        )
        command.clone_options(self)
        return command

    @property
    def create_command(self):
        """Create Command factory for the same platform and format."""
        return self._command_factory("create")

    @property
    def update_command(self):
        """Update Command factory for the same platform and format."""
        return self._command_factory("update")

    @property
    def build_command(self):
        """Build Command factory for the same platform and format."""
        return self._command_factory("build")

    @property
    def run_command(self):
        """Run Command factory for the same platform and format."""
        return self._command_factory("run")

    @property
    def package_command(self):
        """Package Command factory for the same platform and format."""
        return self._command_factory("package")

    @property
    def publish_command(self):
        """Publish Command factory for the same platform and format."""
        return self._command_factory("publish")

    @property
    def platform_path(self):
        """The path for all applications for this command's platform."""
        return self.base_path / self.platform

    def bundle_path(self, app):
        """The path to the bundle for the app in the output format.

        The bundle is the template-generated source form of the app.
        The path will usually be a directory, the existence of which is
        indicative that the template has been rolled out for an app.

        :param app: The app config
        """
        return self.platform_path / self.output_format / app.formal_name

    @abstractmethod
    def binary_path(self, app):
        """The path to the executable artefact for the app in the output
        format.

        This may be a binary file produced by compilation; however, if
        the output format doesn't require compilation, it may be the same
        as the bundle path (assuming the bundle path is inherently
        "executable"), or a path that reasonably represents the thing that can
        be executed.

        :param app: The app config
        """
        ...

    @abstractmethod
    def distribution_path(self, app, packaging_format):
        """The path to the distributable artefact for the app in the given
        packaging format.

        This is the single file that should be uploaded for distribution.
        This may be the binary (if the binary is a self-contained executable);
        however, if the output format produces an installer, it will be the
        path to the installer.

        :param app: The app config
        :param packaging_format: The format of the redistributable artefact.
        """
        ...

    def _load_path_index(self, app: BaseConfig):
        """Load the path index from the index file provided by the app
        template.

        :param app: The config object for the app
        :return: The contents of the application path index.
        """
        with (self.bundle_path(app) / "briefcase.toml").open("rb") as f:
            self._path_index[app] = tomllib.load(f)["paths"]
        return self._path_index[app]

    def support_path(self, app: BaseConfig):
        """Obtain the path into which the support package should be unpacked.

        :param app: The config object for the app
        :return: The full path where the support package should be unpacked.
        """
        # If the index file hasn't been loaded for this app, load it.
        try:
            path_index = self._path_index[app]
        except KeyError:
            path_index = self._load_path_index(app)
        return self.bundle_path(app) / path_index["support_path"]

    def support_revision(self, app: BaseConfig):
        """Obtain the support package revision that the template requires.

        :param app: The config object for the app
        :return: The support revision required by the template.
        """
        # If the index file hasn't been loaded for this app, load it.
        try:
            path_index = self._path_index[app]
        except KeyError:
            path_index = self._load_path_index(app)
        return path_index["support_revision"]

    def cleanup_paths(self, app: BaseConfig):
        """Obtain the paths generated by the app template that should be
        cleaned up prior to release.

        :param app: The config object for the app
        :return: The list of path globs inside the app template that should
            be cleaned up.
        """
        # If the index file hasn't been loaded for this app, load it.
        try:
            path_index = self._path_index[app]
        except KeyError:
            path_index = self._load_path_index(app)
        return path_index["cleanup_paths"]

    def app_requirements_path(self, app: BaseConfig):
        """Obtain the path into which a requirements.txt file should be
        written.

        :param app: The config object for the app
        :return: The full path where the requirements.txt file should be written
        """
        # If the index file hasn't been loaded for this app, load it.
        try:
            path_index = self._path_index[app]
        except KeyError:
            path_index = self._load_path_index(app)
        return self.bundle_path(app) / path_index["app_requirements_path"]

    def app_packages_path(self, app: BaseConfig):
        """Obtain the path into which dependencies should be installed.

        :param app: The config object for the app
        :return: The full path where application dependencies should be installed.
        """
        # If the index file hasn't been loaded for this app, load it.
        try:
            path_index = self._path_index[app]
        except KeyError:
            path_index = self._load_path_index(app)
        return self.bundle_path(app) / path_index["app_packages_path"]

    def app_path(self, app: BaseConfig):
        """Obtain the path into which the application should be installed.

        :param app: The config object for the app
        :return: The full path where application code should be installed.
        """
        # If the index file hasn't been loaded for this app, load it.
        try:
            path_index = self._path_index[app]
        except KeyError:
            path_index = self._load_path_index(app)
        return self.bundle_path(app) / path_index["app_path"]

    def app_module_path(self, app):
        """Find the path for the application module for an app.

        :param app: The config object for the app
        :returns: The Path to the dist-info folder.
        """
        app_home = [
            path.split("/")
            for path in app.sources
            if path.rsplit("/", 1)[-1] == app.module_name
        ]

        if len(app_home) == 0:
            raise BriefcaseCommandError(
                f"Unable to find code for application {app.app_name!r}"
            )
        elif len(app_home) == 1:
            path = Path(str(self.base_path), *app_home[0])
        else:
            raise BriefcaseCommandError(
                f"Multiple paths in sources found for application {app.app_name!r}"
            )

        return path

    @property
    def python_version_tag(self):
        """The major.minor of the Python version in use, as a string.

        This is used as a repository label/tag to identify the
        appropriate templates, etc. to use.
        """
        return (
            f"{self.tools.sys.version_info.major}.{self.tools.sys.version_info.minor}"
        )

    def verify_tools(self):
        """Verify that the tools needed to run this command exist.

        Raises MissingToolException if a required system tool is
        missing.
        """
        pass

    def verify_app_tools(self, app: BaseConfig):
        """Verify that tools needed to run the command for this app exist."""
        pass

    def parse_options(self, extra):
        parser = argparse.ArgumentParser(
            prog=self.cmd_line.format(
                command=self.command,
                platform=self.platform,
                output_format=self.output_format,
            ),
            description=self.description,
        )

        self.add_default_options(parser)
        self.add_options(parser)

        # Parse the full set of command line options from the content
        # remaining after the basic command/platform/output format
        # has been extracted.
        options = vars(parser.parse_args(extra))

        # Extract the base default options onto the command
        self.input.enabled = options.pop("input_enabled")
        self.logger.verbosity = options.pop("verbosity")
        self.logger.save_log = options.pop("save_log")

        return options

    def clone_options(self, command):
        """Clone options from one command to this one.

        :param command: The command whose options are to be cloned
        """
        pass

    def add_default_options(self, parser):
        """Add the default options that exist on *all* commands.

        :param parser: a stub argparse parser for the command.
        """
        parser.add_argument(
            "-v",
            "--verbosity",
            action="count",
            default=1,
            help="set the verbosity of output",
        )
        parser.add_argument("-V", "--version", action="version", version=__version__)
        parser.add_argument(
            "--no-input",
            action="store_false",
            default=True,
            dest="input_enabled",
            help=(
                "Don't ask for user input. If any action would be destructive, "
                "an error will be raised; otherwise, default answers will be "
                "assumed."
            ),
        )
        parser.add_argument(
            "--log",
            action="store_true",
            dest="save_log",
            help="Save a detailed log to file. By default, this log file is only created for critical errors.",
        )

    def add_options(self, parser):
        """Add any options that this command needs to parse from the command
        line.

        :param parser: a stub argparse parser for the command.
        """
        pass

    def parse_config(self, filename):
        try:
            with open(filename, "rb") as config_file:
                # Parse the content of the pyproject.toml file, extracting
                # any platform and output format configuration for each app,
                # creating a single set of configuration options.
                global_config, app_configs = parse_config(
                    config_file,
                    platform=self.platform,
                    output_format=self.output_format,
                )

                self.global_config = create_config(
                    klass=self.GLOBAL_CONFIG_CLASS,
                    config=global_config,
                    msg="Global configuration",
                )

                for app_name, app_config in app_configs.items():
                    # Construct an AppConfig object with the final set of
                    # configuration options for the app.
                    self.apps[app_name] = create_config(
                        klass=self.APP_CONFIG_CLASS,
                        config=app_config,
                        msg=f"Configuration for '{app_name}'",
                    )

        except FileNotFoundError as e:
            raise BriefcaseConfigError(
                f"""Configuration file not found.

Did you run Briefcase in a project directory that contains {filename.name!r}?"""
            ) from e

    def update_cookiecutter_cache(self, template: str, branch="master"):
        """Ensure that we have a current checkout of a template path.

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
                repo = self.tools.git.Repo(cached_template)
                try:
                    # Attempt to update the repository
                    remote = repo.remote(name="origin")
                    remote.fetch()
                except self.tools.git.exc.GitCommandError:
                    # We are offline, or otherwise unable to contact
                    # the origin git repo. It's OK to continue; but warn
                    # the user that the template may be stale.
                    self.logger.warning(
                        """
*************************************************************************
** WARNING: Unable to update template                                  **
*************************************************************************

   Briefcase is unable the update the application template. This
   may be because your computer is currently offline. Briefcase will
   use existing template without updating.

*************************************************************************
"""
                    )
                try:
                    # Check out the branch for the required version tag.
                    head = remote.refs[branch]

                    self.logger.info(
                        f"Using existing template (sha {head.commit.hexsha}, "
                        f"updated {head.commit.committed_datetime.strftime('%c')})"
                    )
                    head.checkout()
                except IndexError as e:
                    # No branch exists for the requested version.
                    raise TemplateUnsupportedVersion(branch) from e
            except self.tools.git.exc.NoSuchPathError:
                # Template cache path doesn't exist.
                # Just use the template directly, rather than attempting an update.
                cached_template = template
            except self.tools.git.exc.InvalidGitRepositoryError:
                # Template cache path exists, but isn't a git repository
                # Just use the template directly, rather than attempting an update.
                cached_template = template
        else:
            # If this isn't a repository URL, treat it as a local directory
            cached_template = template

        return cached_template

    def generate_template(self, template, branch, output_path, extra_context):
        """Ensure the named template is up-to-date for the given branch, and
        roll out that template.

        :param template: The template URL or path to generate
        :param branch: The branch of the template to use
        :param output_path: The filesystem path where the template will be generated.
        :param extra_context: Extra context to pass to the cookiecutter template
        """
        # Make sure we have an updated cookiecutter template,
        # checked out to the right branch
        cached_template = self.update_cookiecutter_cache(
            template=template, branch=branch
        )

        try:
            # Unroll the template
            self.tools.cookiecutter(
                str(cached_template),
                no_input=True,
                output_dir=str(output_path),
                checkout=branch,
                extra_context=extra_context,
            )
        except subprocess.CalledProcessError as e:
            # Computer is offline
            # status code == 128 - certificate validation error.
            raise NetworkFailure("clone template repository") from e
        except cookiecutter_exceptions.RepositoryNotFound as e:
            # Either the template path is invalid,
            # or it isn't a cookiecutter template (i.e., no cookiecutter.json)
            raise InvalidTemplateRepository(template) from e
        except cookiecutter_exceptions.RepositoryCloneFailed as e:
            # Branch does not exist.
            raise TemplateUnsupportedVersion(branch) from e
