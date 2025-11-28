from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

from briefcase.commands.create import _is_local_path
from briefcase.commands.run import RunAppMixin
from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError, RequirementsInstallError
from briefcase.integrations.virtual_environment import VenvContext

from .base import BaseCommand
from .create import write_dist_info


class DevCommand(RunAppMixin, BaseCommand):
    cmd_line = "briefcase dev"
    command = "dev"
    output_format = ""
    description = "Run a Briefcase project in the dev environment."

    # On macOS CoreFoundation/NSApplication will do its own independent parsing of
    # argc/argv. This means that whatever we pass to the Python interpreter on start-up
    # will also be visible to NSApplication which will interpret things like `-u` (used
    # to make I/O unbuffered in CPython) as `-u [URL]` (a request to open a document by
    # URL). This is, rather patently, Not Good.
    # To avoid this causing unwanted hilarity, we use environment variables to configure
    # the Python interpreter rather than command-line options.
    DEV_ENVIRONMENT: Mapping[str, str] = {
        # Equivalent of passing "-u"
        "PYTHONUNBUFFERED": "1",
        # Equivalent of passing "-X dev"
        "PYTHONDEVMODE": "1",
        # Equivalent of passing "-X utf8"
        "PYTHONUTF8": "1",
    }

    @property
    def platform(self):
        """The dev command always reports as the local platform."""
        return {
            "darwin": "macOS",
            "linux": "linux",
            "win32": "windows",
        }[sys.platform]

    def bundle_path(self, app):
        """A placeholder; Dev command doesn't have a bundle path."""
        raise NotImplementedError()

    def binary_path(self, app):
        """A placeholder; Dev command doesn't have a binary path."""
        raise NotImplementedError()

    def add_options(self, parser):
        parser.add_argument("-a", "--app", dest="appname", help="The app to run")
        parser.add_argument(
            "-r",
            "--update-requirements",
            action="store_true",
            help="Update requirements for the app",
        )
        parser.add_argument(
            "--no-run",
            dest="run_app",
            action="store_false",
            default=True,
            help="Do not run the app, just install requirements",
        )
        parser.add_argument(
            "--test",
            dest="test_mode",
            action="store_true",
            help="Run the app in test mode",
        )

    def install_dev_requirements(self, app: AppConfig, venv: VenvContext, **options):
        """Install the requirements for the app dev.

        This will always include test requirements, if specified. Local dependencies are
        installed editable.

        :param app: The config object for the app
        :param venv: The context object used to run commands inside the virtual
            environment.
        """

        requires = app.requires if app.requires else []
        if app.test_requires:
            requires.extend(app.test_requires)
        if not requires:
            self.console.info("No application requirements")
            return

        require_args = []
        for req in requires:
            # Any requirement that is a local path, but *not* a reference to an archive
            # file (zip, whl, etc), can be installed editable. If in doubt, install
            # non-editable.
            if _is_local_path(req) and not _is_archive(req):
                require_args.extend(["-e", req])
            else:
                require_args.append(req)

        with self.console.wait_bar("Installing dev requirements..."):
            try:
                venv.run(
                    [
                        sys.executable,
                        "-u",
                        "-X",
                        "utf8",
                        "-m",
                        "pip",
                        "install",
                        "--upgrade",
                        *(["-vv"] if self.console.is_deep_debug else []),
                        *require_args,
                        *app.requirement_installer_args,
                    ],
                    check=True,
                    encoding="UTF-8",
                )
            except subprocess.CalledProcessError as e:
                raise RequirementsInstallError() from e

    def run_dev_app(
        self,
        app: AppConfig,
        env: dict,
        venv: VenvContext,
        passthrough: list[str],
        **options,
    ):
        """Run the app in the dev environment.

        :param app: The config object for the app
        :param env: environment dictionary for sub command
        :param passthrough: A list of arguments to pass to the app
        """
        main_module = app.main_module()

        # Add in the environment settings to get Python in the state we want.
        # If an environment variable is already defined, don't overwrite it.
        for env_key, env_value in self.DEV_ENVIRONMENT.items():
            env[env_key] = self.tools.os.environ.get(env_key, env_value)

        cmdline = [
            # Do not add additional switches for sys.executable; see DEV_ENVIRONMENT
            sys.executable,
            "-c",
            (
                "import runpy, sys;"
                "sys.path.pop(0);"
                f"sys.argv.extend({passthrough!r});"
                f"runpy.run_module("
                f'"{main_module}", run_name="__main__", alter_sys=True'
                f")"
            ),
        ]

        # Console apps must operate in non-streaming mode so that console input can
        # be handled correctly. However, if we're in test mode, we *must* stream so
        # that we can see the test exit sentinel
        if app.console_app and not app.test_mode:
            self.console.info("=" * 75)
            venv.run(
                cmdline,
                env=env,
                encoding="UTF-8",
                cwd=self.tools.home_path,
                bufsize=1,
                stream_output=False,
            )
        else:
            app_popen = venv.Popen(
                cmdline,
                env=env,
                encoding="UTF-8",
                cwd=self.tools.home_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            )

            # Start streaming logs for the app.
            self._stream_app_logs(
                app,
                popen=app_popen,
                clean_output=False,
            )

    def get_environment(self, app: AppConfig):
        """Create a shell environment where PYTHONPATH points to the source directories
        described by the app config.

        :param app: The config object for the app
        """

        env = {
            "PYTHONPATH": os.pathsep.join(
                os.fsdecode(Path.cwd() / path) for path in app.PYTHONPATH()
            )
        }

        # On Windows, we need to disable the debug allocator because it
        # conflicts with Python.net. See
        # https://github.com/pythonnet/pythonnet/issues/1977 for details.
        if self.platform == "windows":  # pragma: no branch
            env["PYTHONMALLOC"] = "default"  # pragma: no-cover-if-not-windows

        # If we're in verbose mode, put BRIEFCASE_DEBUG into the environment
        if self.console.is_debug:
            env["BRIEFCASE_DEBUG"] = "1"

        return env

    @property
    def venv_name(self) -> str:
        """Returns the name of the virtual environment directory.

        :returns: Name for virtual environment directory
        """
        return "dev"

    def venv_path(self, appname: str) -> Path:
        """Return the path for the app's virtual environment.

        :param app: The app config
        :returns: Path where the venv should be located
        """
        return self.base_path / ".briefcase" / appname / self.venv_name

    def __call__(
        self,
        appname: str | None = None,
        update_requirements: bool | None = False,
        run_app: bool | None = True,
        test_mode: bool | None = False,
        passthrough: list[str] | None = None,
        **options,
    ):
        # Which app should we run? If there's only one defined
        # in pyproject.toml, then we can use it as a default;
        # otherwise look for a -a/--app option.
        if len(self.apps) == 1:
            app = next(iter(self.apps.values()))
        elif appname:
            try:
                app = self.apps[appname]
            except KeyError as e:
                raise BriefcaseCommandError(
                    f"Project doesn't define an application named '{appname}'"
                ) from e

        else:
            # Multiple apps, and no explicit --app was provided.
            # If --no-input was passed, do not prompt - raise error.
            if not self.console.input_enabled:
                raise BriefcaseCommandError(
                    "Project specifies more than one application; "
                    "use --app to specify which one to start."
                )

            # Build mapping for {app_name: formal_name} for selection menu.
            app_options = {
                app_name: app_config.formal_name
                for app_name, app_config in self.apps.items()
            }

            # Default app is the first listed in the config file
            default_app_name = next(iter(self.apps.keys()))

            # Display interactive menu to select the app
            selected_app_name = self.console.selection_question(
                description="Start dev app",
                intro=(
                    "Your project defines multiple applications. "
                    "Which application would you like to start (in dev mode)?"
                ),
                options=app_options,
                default=default_app_name,
            )

            # Use the selected app
            app = self.apps[selected_app_name]

        # Confirm host compatibility, that all required tools are available,
        # and that the app configuration is finalized.
        self.finalize(app, test_mode)

        self.verify_app(app)

        if not run_app:
            # If we are not running the app, it means we should update requirements.
            update_requirements = True

        with self.tools.virtual_environment.create(
            venv_path=self.venv_path(app.app_name),
            isolated=options.get("isolated", False),
            recreate=update_requirements,
        ) as venv:
            if venv.created:
                self.console.info("Installing requirements...", prefix=app.app_name)
                self.install_dev_requirements(app, venv, **options)
                write_dist_info(
                    app,
                    self.app_module_path(app).parent / app.dist_info_name,
                )

            if run_app:
                if app.test_mode:
                    self.console.info(
                        "Running test suite in dev environment...", prefix=app.app_name
                    )
                else:
                    self.console.info("Starting in dev mode...", prefix=app.app_name)
                return self.run_dev_app(
                    app,
                    env=self.get_environment(app),
                    venv=venv,
                    passthrough=[] if passthrough is None else passthrough,
                    **options,
                )


def _is_archive(filename):
    """Determine if the file is an archive file.

    :param filename: The path to check
    :returns: True if the file is an archive.
    """
    return any(
        filename.endswith(ext)
        for ext in [".tar.gz", ".tar.bz2", ".tar", ".zip", ".whl"]
    )
