from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from briefcase.commands.run import RunAppMixin
from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError, RequirementsInstallError

from .base import BaseCommand
from .create import write_dist_info


class DevCommand(RunAppMixin, BaseCommand):
    cmd_line = "briefcase dev"
    command = "dev"
    output_format = None
    description = "Run a Briefcase project in the dev environment."

    # On macOS CoreFoundation/NSApplication will do its own independent parsing of argc/argv.
    # This means that whatever we pass to the Python interpreter on start-up will also be
    # visible to NSApplication which will interpret things like `-u` (used to make I/O
    # unbuffered in CPython) as `-u [URL]` (a request to open a document by URL). This is,
    # rather patently, Not Good.
    # To avoid this causing unwanted hilarity, we use environment variables to configure the
    # Python interpreter rather than command-line options.
    DEV_ENVIRONMENT = {
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

    def install_dev_requirements(self, app: AppConfig, **options):
        """Install the requirements for the app dev.

        This will always include test requirements, if specified.

        :param app: The config object for the app
        """
        requires = app.requires if app.requires else []
        if app.test_requires:
            requires.extend(app.test_requires)

        if requires:
            with self.input.wait_bar("Installing dev requirements..."):
                try:
                    self.tools.subprocess.run(
                        [
                            sys.executable,
                            "-u",
                            "-X",
                            "utf8",
                            "-m",
                            "pip",
                            "install",
                            "--upgrade",
                        ]
                        + (["-vv"] if self.logger.is_deep_debug else [])
                        + requires,
                        check=True,
                        encoding="UTF-8",
                    )
                except subprocess.CalledProcessError as e:
                    raise RequirementsInstallError() from e
        else:
            self.logger.info("No application requirements.")

    def run_dev_app(
        self,
        app: AppConfig,
        env: dict,
        test_mode: bool,
        passthrough: list[str],
        **options,
    ):
        """Run the app in the dev environment.

        :param app: The config object for the app
        :param env: environment dictionary for sub command
        :param test_mode: Run the test suite, rather than the app?
        :param passthrough: A list of arguments to pass to the app
        """
        main_module = app.main_module(test_mode)

        # Add in the environment settings to get Python in the state we want.
        env.update(self.DEV_ENVIRONMENT)

        cmdline = [
            # Do not add additional switches for sys.executable; see DEV_ENVIRONMENT
            sys.executable,
            "-c",
            (
                "import runpy, sys;"
                "sys.path.pop(0);"
                f"sys.argv.extend({passthrough!r});"
                f'runpy.run_module("{main_module}", run_name="__main__", alter_sys=True)'
            ),
        ]

        # Console apps must operate in non-streaming mode so that console input can
        # be handled correctly. However, if we're in test mode, we *must* stream so
        # that we can see the test exit sentinel
        if app.console_app and not test_mode:
            self.logger.info("=" * 75)
            self.tools.subprocess.run(
                cmdline,
                env=env,
                encoding="UTF-8",
                cwd=self.tools.home_path,
                bufsize=1,
                stream_output=False,
            )
        else:
            app_popen = self.tools.subprocess.Popen(
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
                test_mode=test_mode,
                clean_output=False,
            )

    def get_environment(self, app, test_mode: bool):
        # Create a shell environment where PYTHONPATH points to the source
        # directories described by the app config.
        env = {
            "PYTHONPATH": os.pathsep.join(
                os.fsdecode(Path.cwd() / path) for path in app.PYTHONPATH(test_mode)
            )
        }

        # On Windows, we need to disable the debug allocator because it
        # conflicts with Python.net. See
        # https://github.com/pythonnet/pythonnet/issues/1977 for details.
        if self.platform == "windows":  # pragma: no branch
            env["PYTHONMALLOC"] = "default"  # pragma: no-cover-if-not-windows

        # If we're in verbose mode, put BRIEFCASE_DEBUG into the environment
        if self.logger.is_debug:
            env["BRIEFCASE_DEBUG"] = "1"

        return env

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
            app = list(self.apps.values())[0]
        elif appname:
            try:
                app = self.apps[appname]
            except KeyError as e:
                raise BriefcaseCommandError(
                    f"Project doesn't define an application named '{appname}'"
                ) from e

        else:
            raise BriefcaseCommandError(
                "Project specifies more than one application; use --app to specify which one to start."
            )
        # Confirm host compatibility, that all required tools are available,
        # and that the app configuration is finalized.
        self.finalize(app)

        self.verify_app(app)

        # Look for the existence of a dist-info file.
        # If one exists, assume that the requirements have already been
        # installed. If a dependency update has been manually requested,
        # do it regardless.
        dist_info_path = (
            self.app_module_path(app).parent / f"{app.module_name}.dist-info"
        )
        if not run_app:
            # If we are not running the app, it means we should update requirements.
            update_requirements = True
        if update_requirements or not dist_info_path.exists():
            self.logger.info("Installing requirements...", prefix=app.app_name)
            self.install_dev_requirements(app, **options)
            write_dist_info(app, dist_info_path)

        if run_app:
            if test_mode:
                self.logger.info(
                    "Running test suite in dev environment...", prefix=app.app_name
                )
            else:
                self.logger.info("Starting in dev mode...", prefix=app.app_name)
            env = self.get_environment(app, test_mode=test_mode)
            return self.run_dev_app(
                app,
                env,
                test_mode=test_mode,
                passthrough=[] if passthrough is None else passthrough,
                **options,
            )
