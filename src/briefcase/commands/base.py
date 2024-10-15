from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import inspect
import os
import platform
import subprocess
import sys
from abc import ABC, abstractmethod
from argparse import RawDescriptionHelpFormatter
from pathlib import Path
from typing import Any

from cookiecutter import exceptions as cookiecutter_exceptions
from cookiecutter.repository import is_repo_url
from packaging.specifiers import InvalidSpecifier, Specifier
from packaging.version import Version
from platformdirs import PlatformDirs

if sys.version_info >= (3, 11):  # pragma: no-cover-if-lt-py311
    import tomllib
else:  # pragma: no-cover-if-gte-py311
    import tomli as tomllib

import briefcase
from briefcase import __version__
from briefcase.config import AppConfig, GlobalConfig, parse_config
from briefcase.console import MAX_TEXT_WIDTH, Console, Log
from briefcase.exceptions import (
    BriefcaseCommandError,
    BriefcaseConfigError,
    InvalidTemplateRepository,
    MissingAppMetadata,
    NetworkFailure,
    TemplateUnsupportedVersion,
    UnsupportedHostError,
    UnsupportedPythonVersion,
)
from briefcase.integrations.base import ToolCache
from briefcase.integrations.file import File
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms import get_output_formats, get_platforms


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


def split_passthrough(args):
    try:
        pos = args.index("--")
    except ValueError:
        return args, []
    else:
        return args[:pos], args[pos + 1 :]


def parse_config_overrides(config_overrides: list[str] | None) -> dict[str, Any]:
    """Parse command line -C/--config option overrides.

    :param config_overrides: The values passed in as configuration overrides. Each value
        *should* be a "key=<valid TOML>" string.
    :returns: A dictionary of app configuration keys to override and their new values.
    :raises BriefcaseCommandError: if any of the values can't be parsed as valid TOML.
    """
    overrides = {}
    if config_overrides:
        for override in config_overrides:
            try:
                # Do initial checks of the key being overridden.
                # These catch cases that would be valid TOML, but would result
                # in invalid app configurations.
                key, _ = override.split("=", 1)
                if "." in key:
                    raise BriefcaseConfigError(
                        "Can't override multi-level configuration keys."
                    )
                elif key == "app_name":
                    raise BriefcaseConfigError("The app name cannot be overridden.")

                # Now actually parse the value
                overrides.update(tomllib.loads(override))
            except ValueError as e:
                raise BriefcaseConfigError(
                    f"Unable to parse configuration override {override}"
                ) from e
    return overrides


class BaseCommand(ABC):
    cmd_line = "briefcase {command} {platform} {output_format}"
    supported_host_os = {"Darwin", "Linux", "Windows"}
    supported_host_os_reason = f"This command is not supported on {platform.system()}."

    # defined by platform-specific subclasses
    command: str
    description: str
    platform: str
    output_format: str
    # supports passing extra command line arguments to subprocess
    allows_passthrough = False
    # if specified for a platform, then any template for that platform must declare
    # compatibility with that version epoch. An epoch begins when a breaking change is
    # introduced for a platform such that older versions of a template are incompatible
    platform_target_version: str | None = None

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
        :param is_clone: Flag that Command was triggered by the user's requested
            Command; for instance, RunCommand can invoke UpdateCommand and/or
            BuildCommand.
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

        # Immediately add tools that must be always available
        Subprocess.verify(tools=self.tools)
        File.verify(tools=self.tools)

        if not is_clone:
            self.validate_locale()

        self.global_config = None
        self._briefcase_toml: dict[AppConfig, dict[str, ...]] = {}

    @property
    def logger(self):
        return self.tools.logger

    @property
    def input(self):
        return self.tools.input

    def validate_data_path(self, data_path):
        """Validate provided data path or determine OS-specific path.

        If a data path is provided during construction, use it. This usually indicates
        we're under test conditions. If there's no data path provided, look for a
        BRIEFCASE_HOME environment variable. If that isn't defined, use a platform-
        specific default data path.
        """
        if data_path is None:
            try:
                briefcase_home = os.environ["BRIEFCASE_HOME"]
                data_path = Path(briefcase_home).resolve()
                # Path("") converts to ".", so check for that edge case.
                if briefcase_home == "" or not data_path.is_dir():
                    raise BriefcaseCommandError(
                        "The path specified by BRIEFCASE_HOME does not exist."
                    )
            except KeyError:
                if platform.system() == "Darwin":  # pragma: no-cover-if-not-macos
                    # macOS uses a bundle name, rather than just the app name
                    app_name = "org.beeware.briefcase"
                else:  # pragma: no-cover-if-is-macos
                    app_name = "briefcase"

                data_path = PlatformDirs(
                    appname=app_name,
                    appauthor="BeeWare",
                ).user_cache_path

        data_path = os.fsdecode(data_path)

        if " " in data_path:
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

        if not os.path.exists(data_path):
            try:
                # The Windows Store version of Python can redirect filesystem
                # interactions within %LOCALAPPDATA% to a sandboxed location.
                # To bypass this, the Briefcase cache directory creation is
                # performed via ``cmd.exe`` in a different process. Once this
                # directory exists in the "real" %LOCALAPPDATA%, Windows will
                # allow normal interactions without attempting to sandbox them.
                if platform.system() == "Windows":  # pragma: no-cover-if-not-windows
                    subprocess.run(
                        ["mkdir", data_path],
                        shell=True,
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:  # pragma: no-cover-if-is-windows
                    os.makedirs(data_path, exist_ok=True)
            except (subprocess.CalledProcessError, OSError):
                raise BriefcaseCommandError(
                    f"""
Failed to create the Briefcase directory to store tools and support files:

    {data_path}

You can set the environment variable BRIEFCASE_HOME to specify
a custom location for Briefcase's tools.

"""
                )

        return Path(data_path)

    def validate_locale(self):
        """Validate the system's locale is compatible."""
        if self.tools.host_os == "Linux" and self.tools.system_encoding != "UTF-8":
            self.logger.warning(
                f"""
*************************************************************************
** WARNING: Default system encoding is not supported                   **
*************************************************************************

    Briefcase and the third-party tools it uses only support UTF-8.

    The detected default system encoding is {self.tools.system_encoding}.

    Briefcase will proceed but some console output could be corrupted and
    created files or artefacts may contain corrupted text.

    Update your system's encoding to UTF-8 to avoid issues.

*************************************************************************
"""
            )

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

    def template_cache_path(self, template) -> Path:
        """The path where Briefcase keeps template checkouts.

        :param template: The URL for the template that will be cached locally.
        """
        template = template.rstrip("/")
        tail = template.split("/")[-1]
        cache_name = tail.rsplit(".git")[0]
        return self.data_path / "templates" / cache_name

    def build_path(self, app) -> Path:
        """The path in which all platform artefacts for the app will be built.

        :param app: The app config
        """
        return self.base_path / "build" / app.app_name / self.platform.lower()

    @property
    def dist_path(self) -> Path:
        """The path for all applications for this command's platform."""
        return self.base_path / "dist"

    def bundle_path(self, app) -> Path:
        """The path to the bundle for the app in the output format.

        The bundle is the template-generated source form of the app. The path will
        usually be a directory, the existence of which is indicative that the template
        has been rolled out for an app. The leaf of this path is the base of the content
        generated from template.

        :param app: The app config
        """
        return self.build_path(app) / self.output_format.lower()

    @abstractmethod
    def binary_path(self, app) -> Path:
        """The path to the executable artefact for the app in the output format.

        This may be a binary file produced by compilation; however, if the output format
        doesn't require compilation, it may be the same as the bundle path (assuming the
        bundle path is inherently "executable"), or a path that reasonably represents
        the thing that can be executed.

        :param app: The app config
        """

    def binary_executable_path(self, app) -> Path:
        """The path to the actual binary object for the app in the output format.

        For most platforms, this will be the same as the binary path. However, for
        platforms that use an "executable bundle" (e.g., macOS), this will be actual
        binary that is embedded in the bundle.

        :param app: The app config
        """
        return self.binary_path(app)

    def unbuilt_executable_path(self, app) -> Path:
        """The path to the unbuilt form of the binary object for the app.

        The pre-built stub binary may need to undergo some manipulation before it can be
        used; to mark that this manipulation is required, the "unbuilt" binary has a
        "raw" name that doesn't involve any app details. The build step moves the binary
        to the final name.

        :param app: The app config
        """
        return self.binary_executable_path(app).parent / (
            "Stub" + self.binary_executable_path(app).suffix
        )

    def briefcase_toml(self, app: AppConfig) -> dict[str, ...]:
        """Load the ``briefcase.toml`` file provided by the app template.

        :param app: The config object for the app
        :return: The contents of ``briefcase.toml``
        """
        try:
            return self._briefcase_toml[app]
        except KeyError:
            try:
                with (self.bundle_path(app) / "briefcase.toml").open("rb") as f:
                    self._briefcase_toml[app] = tomllib.load(f)
            except OSError as e:
                raise MissingAppMetadata(self.bundle_path(app)) from e
            else:
                return self._briefcase_toml[app]

    def path_index(self, app: AppConfig, path_name: str) -> str | dict | list:
        """Return a path from the path index provided by the app template.

        Raises KeyError if ``path_name`` is not defined in the index.

        :param app: The config object for the app
        :param path_name: Name of the filepath to retrieve
        :return: filepath for requested path
        """
        return self.briefcase_toml(app)["paths"][path_name]

    def template_target_version(self, app: AppConfig) -> str | None:
        """The target version of Briefcase for the app from ``briefcase.toml``.

        This value represents a version epoch specific to the platform. An epoch begins
        when a breaking change is introduced. Therefore, this value would remain the
        version of Briefcase that introduced a breaking change for a template until
        another such change requires a new epoch.

        :param app: The config object for the app
        :return: target version or None if one isn't specified
        """
        try:
            return self.briefcase_toml(app)["briefcase"]["target_version"]
        except KeyError:
            return None

    def stub_binary_revision(self, app: AppConfig) -> str:
        """Obtain the stub binary revision that the template requires.

        :param app: The config object for the app
        :return: The stub binary revision required by the template.
        """
        return self.path_index(app, "stub_binary_revision")

    def support_path(self, app: AppConfig) -> Path:
        """Obtain the path into which the support package should be unpacked.

        :param app: The config object for the app
        :return: The full path where the support package should be unpacked.
        """
        return self.bundle_path(app) / self.path_index(app, "support_path")

    def support_revision(self, app: AppConfig) -> str:
        """Obtain the support package revision that the template requires.

        :param app: The config object for the app
        :return: The support revision required by the template.
        """
        return self.path_index(app, "support_revision")

    def cleanup_paths(self, app: AppConfig) -> list[str]:
        """Obtain the paths generated by the app template that should be cleaned up
        prior to release.

        :param app: The config object for the app
        :return: The list of path globs inside the app template that should be cleaned
            up.
        """
        return self.path_index(app, "cleanup_paths")

    def app_requirements_path(self, app: AppConfig) -> Path:
        """Obtain the path into which a requirements.txt file should be written.

        :param app: The config object for the app
        :return: The full path where the requirements.txt file should be written
        """
        return self.bundle_path(app) / self.path_index(app, "app_requirements_path")

    def app_packages_path(self, app: AppConfig) -> Path:
        """Obtain the path into which requirements should be installed.

        :param app: The config object for the app
        :return: The full path where application requirements should be installed.
        """
        return self.bundle_path(app) / self.path_index(app, "app_packages_path")

    def app_path(self, app: AppConfig) -> Path:
        """Obtain the path into which the application should be installed.

        :param app: The config object for the app
        :return: The full path where application code should be installed.
        """
        return self.bundle_path(app) / self.path_index(app, "app_path")

    def app_module_path(self, app: AppConfig) -> Path:
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
    def briefcase_required_python_version(self):
        """The major.minor of the minimum Python version required by Briefcase itself.

        This is extracted from packaging metadata.
        """
        # Native format is ">=3.8"
        return tuple(
            int(v)
            for v in importlib.metadata.metadata("briefcase")["Requires-Python"]
            .split("=")[1]
            .strip()
            .split(".")
        )

    @property
    def python_version_tag(self):
        """The major.minor of the Python version in use, as a string.

        This is used as a repository label/tag to identify the appropriate templates,
        etc. to use.
        """
        return (
            f"{self.tools.sys.version_info.major}.{self.tools.sys.version_info.minor}"
        )

    def verify_host(self):
        """Verify the host OS is supported by the Command."""
        if self.tools.host_os not in self.supported_host_os:
            raise UnsupportedHostError(self.supported_host_os_reason)

    def verify_tools(self):
        """Verify that the tools needed to run this Command exist.

        Raises MissingToolException if a required system tool is missing.
        """

    def finalize_app_config(self, app: AppConfig):
        """Finalize the application config.

        Some app configurations (notably, Linux system packages like .deb) have
        configurations that are deeper than other platforms, because they need to
        include components that are dependent on command-line arguments. They may also
        require the existence of system tools to complete configuration.

        The final app configuration merges those "deep" properties into the app
        configuration, and performs any other app-specific platform configuration and
        verification that is required as a result of command-line arguments.

        :param app: The app configuration to finalize.
        """

    def finalize(self, app: AppConfig | None = None):
        """Finalize Briefcase configuration.

        This will:

        1. Ensure that the host has been verified
        2. Ensure that the platform tools have been verified
        3. Ensure that app configurations have been finalized.

        App finalization will only occur once per invocation.

        :param app: If provided, the specific app configuration
            to finalize. By default, all apps will be finalized.
        """
        self.verify_host()
        self.verify_tools()

        if app is None:
            for app in self.apps.values():
                if hasattr(app, "__draft__"):
                    self.finalize_app_config(app)
                    delattr(app, "__draft__")
        else:
            if hasattr(app, "__draft__"):
                self.finalize_app_config(app)
                delattr(app, "__draft__")

    def verify_app(self, app: AppConfig):
        """Verify the app is compatible and the app tools are available.

        This is the last step of verification for a Command before running the Command's
        business logic. It runs _after_ pre-requisite Commands have been verified and
        run.

        :param app: app configuration
        """
        self.verify_app_template(app)
        self.verify_app_tools(app)
        self.verify_required_python(app)

    def verify_app_tools(self, app: AppConfig):
        """Verify that tools needed to run the command for this app exist."""

    def verify_app_template(self, app: AppConfig):
        """Verify the template targets the same Briefcase version as the Command.

        :param app: app configuration
        """

        # Skip this check if the template isn't rolled out
        # or if the command doesn't support templates
        try:
            template_target_version = self.template_target_version(app)
        except (MissingAppMetadata, NotImplementedError):
            return

        if self.platform_target_version != template_target_version:
            raise BriefcaseCommandError(
                f"""\
The app template used to generate this app is not compatible with this version
of Briefcase.

If the app was generated with an earlier version of Briefcase using the default
Briefcase template, you can run:

     $ briefcase create {self.platform} {self.output_format}

to re-generate your app with a compatible version of the template.

If you are using a custom template, you'll need to update the template to correct
any compatibility problems, and then add the compatibility declaration.
"""
            )

    def verify_required_python(self, app: AppConfig):
        """Verify that the running version of Python meets the project's specifications."""

        requires_python = getattr(self.global_config, "requires_python", None)
        if not requires_python:
            return

        try:
            spec = Specifier(requires_python)
        except InvalidSpecifier as e:
            raise BriefcaseConfigError(
                f"Invalid requires-python in pyproject.toml: {e}"
            ) from e

        running_version = platform.python_version()

        if not spec.contains(running_version):
            raise UnsupportedPythonVersion(
                version_specifier=requires_python, running_version=running_version
            )

    def parse_options(self, extra):
        """Parse the command line arguments for the Command.

        After the initial ArgumentParser runs to choose the Command for the selected
        platform and format, a new ArgumentParser is created here to parse the remaining
        command line arguments specific to the Command. Additionally, the default
        options for disabling input, log verbosity, and log saving are parsed out and
        saved to the Command.

        :param extra: the remaining command line arguments after the initial
            ArgumentParser runs over the command line.
        :return: dictionary of parsed arguments for Command, and a dictionary of parsed
            configuration overrides.
        """
        default_format = getattr(
            get_platforms().get(self.platform), "DEFAULT_OUTPUT_FORMAT", None
        )
        # only show supported formats for Commands that support formats
        if default_format is not None and self.command not in {"new", "dev", "upgrade"}:
            formats = list(get_output_formats(self.platform).keys())
            formats[formats.index(default_format)] = f"{default_format} (default)"
            supported_formats_helptext = (
                f"Supported formats:\n  {', '.join(sorted(formats, key=str.lower))}"
            )
        else:
            supported_formats_helptext = ""

        parser = argparse.ArgumentParser(
            prog=self.cmd_line.format(
                command=self.command,
                platform=self.platform,
                output_format=self.output_format,
            ),
            description=self.input.textwrap(
                f"{self.description}\n\n{supported_formats_helptext}"
            ),
            formatter_class=(
                lambda prog: RawDescriptionHelpFormatter(prog, width=MAX_TEXT_WIDTH)
            ),
        )

        self.add_default_options(parser)
        self.add_options(parser)

        # If the command allows passthrough arguments, add an option for the help,
        # then process the argument list to strip out the passthrough args.
        if self.allows_passthrough:
            parser.add_argument(
                "--",
                dest="passthrough",
                metavar="ARGS ...",
                required=False,
                help="Arguments to pass to the app",
            )
            args, passthrough = split_passthrough(extra)
        else:
            args = extra

        # Parse the full set of command line options from the content
        # remaining after the basic command/platform/output format
        # has been extracted.
        options = vars(parser.parse_args(args))

        if self.allows_passthrough:
            options["passthrough"] = passthrough

        # Extract the base default options onto the command
        self.input.enabled = options.pop("input_enabled")
        self.logger.verbosity = options.pop("verbosity")
        self.logger.save_log = options.pop("save_log")

        # Parse the configuration overrides
        overrides = parse_config_overrides(options.pop("config_overrides"))

        return options, overrides

    def clone_options(self, command):
        """Clone options from one command to this one.

        :param command: The command whose options are to be cloned
        """

    def add_default_options(self, parser):
        """Add the default options that exist on *all* commands.

        :param parser: a stub argparse parser for the command.
        """
        parser.add_argument(
            "-C",
            "--config",
            dest="config_overrides",
            action="append",
            metavar="KEY=VALUE",
            help="Override the value of the app configuration item KEY with VALUE",
        )
        parser.add_argument(
            "-v",
            "--verbosity",
            action="count",
            default=0,
            help="Enable verbose logging. Use -vv and -vvv to increase logging verbosity",
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
                "assumed"
            ),
        )
        parser.add_argument(
            "--log",
            action="store_true",
            dest="save_log",
            help="Save a detailed log to file. By default, this log file is only created for critical errors",
        )

    def _add_update_options(
        self,
        parser,
        context_label="",
        update=True,
    ):
        """Internal utility method for adding common update options.

        :param parser: The parser to which options should be added.
        :param context_label: Label text that will be added to the end of the help text
            to describe when the update will be applied (e.g., "before building")
        :param update: Should the --update and --no-update options be exposed?
        """
        if update:
            parser.add_argument(
                "-u",
                "--update",
                action="store_true",
                help=f"Update the app{context_label}",
            )

        parser.add_argument(
            "-r",
            "--update-requirements",
            action="store_true",
            help=f"Update requirements for the app{context_label}",
        )

        parser.add_argument(
            "--update-support",
            action="store_true",
            help=f"Update support package for the app{context_label}",
        )

        parser.add_argument(
            "--update-stub",
            action="store_true",
            help=f"Update stub binary for the app{context_label}",
        )

        parser.add_argument(
            "--update-resources",
            action="store_true",
            help=f"Update app resources (icons, splash screens, etc){context_label}",
        )

        if update:
            parser.add_argument(
                "--no-update",
                action="store_true",
                help=f"Prevent any automated update{context_label}",
            )

    def _add_test_options(self, parser, context_label):
        """Internal utility method for adding common test-related options.

        :param parser: The parser to which options should be added.
        :param context_label: Label text for commands; the capitalized action being
            performed (e.g., "Build", "Run",...)
        """
        parser.add_argument(
            "--test",
            dest="test_mode",
            action="store_true",
            help=f"{context_label} the app in test mode",
        )

    def add_options(self, parser):
        """Add any options that this command needs to parse from the command line.

        :param parser: a stub argparse parser for the command.
        """

    def parse_config(self, filename, overrides):
        try:
            with open(filename, "rb") as config_file:
                # Parse the content of the pyproject.toml file, extracting
                # any platform and output format configuration for each app,
                # creating a single set of configuration options.
                global_config, app_configs = parse_config(
                    config_file,
                    platform=self.platform,
                    output_format=self.output_format,
                    logger=self.logger,
                )

                # Create the global config
                global_config.update(overrides)
                self.global_config = create_config(
                    klass=GlobalConfig,
                    config=global_config,
                    msg="Global configuration",
                )

                for app_name, app_config in app_configs.items():
                    # Construct an AppConfig object with the final set of
                    # configuration options for the app.
                    app_config.update(overrides)
                    self.apps[app_name] = create_config(
                        klass=AppConfig,
                        config=app_config,
                        msg=f"Configuration for '{app_name}'",
                    )

        except OSError as e:
            raise BriefcaseConfigError(
                f"""\
Configuration file not found.

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
            # Look for a Briefcase cache of the template.
            cached_template = self.template_cache_path(template)

            if cached_template.exists():
                # There is a pre-existing cache of the template. Attempt to update it;
                # if the fetch fails, use the existing state of the cache. Any other
                # failure is surfaced to the user.
                try:
                    repo = self.tools.git.Repo(cached_template)
                except self.tools.git.exc.GitError:
                    # Template repository is in a weird state. Delete it
                    self.logger.warning(
                        "Template cache is in a weird state. Getting a clean clone."
                    )
                    self.tools.shutil.rmtree(cached_template)

            if not cached_template.exists():
                # There's no pre-existing template. It's either the first time seeing
                # the template, or the template was in a weird state. Perform a blobless
                # clone.
                try:
                    self.logger.info(f"Cloning template {template!r}...")
                    cached_template.mkdir(exist_ok=True, parents=True)
                    repo = self.tools.git.Repo.clone_from(
                        url=template,
                        to_path=cached_template,
                        filter=["blob:none"],
                        no_checkout=True,
                    )
                except KeyboardInterrupt:
                    # The user has aborted the initial clone. Git is fairly resilient to
                    # being interrupted, but if the *initial* clone fails, it's very
                    # hard to recover. To avoid problems on the next run, remove the
                    # partial repo clone.
                    if cached_template.exists():
                        self.tools.shutil.rmtree(cached_template)
                    raise
                except self.tools.git.exc.GitError as e:
                    # The clone failed; to make sure the repo is in a clean state, clean up
                    # any partial remnants of this initial clone.
                    # If we're getting a GitError, we know the directory must exist.
                    self.tools.shutil.rmtree(cached_template)
                    raise BriefcaseCommandError(
                        f"Unable to clone repository {template!r}.\n"
                        "\n"
                        "This may be because your computer is offline, or "
                        "because the repository URL is incorrect."
                    ) from e

            try:
                # Raises ValueError if "origin" isn't a valid remote
                remote = repo.remote(name="origin")
                # Ensure the existing repo's origin URL points to the location
                # being requested. A difference can occur, for instance, if a
                # fork of the template is used.
                remote.set_url(new_url=template, old_url=remote.url)
                try:
                    # Attempt to update the repository
                    remote.fetch()
                except self.tools.git.exc.GitCommandError as e:
                    # We are offline, or otherwise unable to contact the origin git
                    # repo. It's OK to continue; but capture the error in the log and
                    # warn the user that the template may be stale.
                    self.logger.debug(str(e))
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
            except (ValueError, self.tools.git.exc.GitError) as e:
                raise BriefcaseCommandError(
                    "Unable to check out template branch.\n"
                    "\n"
                    "This may be because your computer is offline, or because the template repository\n"
                    "is in a weird state. If you have a stable network connection, try deleting:\n"
                    "\n"
                    f"    {cached_template}\n"
                    "\n"
                    "and retrying your command."
                ) from e
        else:
            # If this isn't a repository URL, treat it as a local directory
            cached_template = template

        return cached_template

    def _generate_template(self, template, branch, output_path, extra_context):
        """Ensure the named template is up-to-date for the given branch, and roll out
        that template.

        :param template: The template URL or path to generate
        :param branch: The branch of the template to use
        :param output_path: The filesystem path where the template will be generated.
        :param extra_context: Extra context to pass to the cookiecutter template
        """
        # Make sure we have an updated cookiecutter template,
        # checked out to the right branch
        cached_template = self.update_cookiecutter_cache(
            template=template,
            branch=branch,
        )

        self.logger.configure_stdlib_logging("cookiecutter")
        try:
            # Unroll the template.
            self.tools.cookiecutter(
                str(cached_template),
                no_input=True,
                output_dir=str(output_path),
                checkout=branch,
                # Use a copy to prevent changes propagating among tests while test suite is running
                extra_context=extra_context.copy(),
                # Store replay data in the Briefcase template cache instead of ~/.cookiecutter_replay
                default_config={"replay_dir": str(self.template_cache_path(".replay"))},
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
        except cookiecutter_exceptions.UndefinedVariableInTemplate as e:
            raise BriefcaseConfigError(e.message) from e

    def generate_template(
        self,
        template: str | None,
        branch: str | None,
        output_path: str | Path,
        extra_context: dict[str, str],
    ) -> None:
        # If a branch wasn't supplied through the --template-branch argument,
        # use the branch derived from the Briefcase version
        version = Version(briefcase.__version__)
        if branch is None:
            template_branch = f"v{version.base_version}"
        else:
            template_branch = branch

        extra_context = extra_context.copy()
        # Additional context that can be used for the Briefcase template pyproject.toml
        # header to include the version of Briefcase as well as the source of the template.
        extra_context.update(
            {
                "template_source": template,
                "template_branch": template_branch,
                "briefcase_version": str(version),
            }
        )

        try:
            self.logger.info(
                f"Using app template: {template}, branch {template_branch}"
            )
            # Unroll the new app template
            self._generate_template(
                template=template,
                branch=template_branch,
                output_path=output_path,
                extra_context=extra_context,
            )
        except TemplateUnsupportedVersion:
            # Only use the main template if we're on a development branch of briefcase
            # and the user didn't explicitly specify which branch to use.
            if version.dev is None or branch is not None:
                raise

            # Development branches can use the main template.
            self.logger.info(
                f"Template branch {template_branch} not found; falling back to development template"
            )

            extra_context["template_branch"] = "main"
            self._generate_template(
                template=template,
                branch="main",
                output_path=output_path,
                extra_context=extra_context,
            )
