import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError

from .base import BaseCommand
from .create import DependencyInstallError, write_dist_info


class DevCommand(BaseCommand):
    cmd_line = "briefcase dev"
    command = "dev"
    output_format = None
    description = "Run a briefcase project in the dev environment"

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

    def distribution_path(self, app, packaging_format):
        """A placeholder; Dev command doesn't have a distribution path."""
        raise NotImplementedError()

    def add_options(self, parser):
        parser.add_argument("-a", "--app", dest="appname", help="The app to run")
        parser.add_argument(
            "-d",
            "--update-dependencies",
            action="store_true",
            help="Update dependencies for app",
        )
        parser.add_argument(
            "--no-run",
            dest="run_app",
            action="store_false",
            default=True,
            help="Do not run the app, just install dependencies.",
        )

    def install_dev_dependencies(self, app: BaseConfig, **options):
        """Install the dependencies for the app devly.

        :param app: The config object for the app
        """
        if app.requires:
            with self.input.wait_bar("Installing dev dependencies..."):
                try:
                    self.tools.subprocess.run(
                        [
                            sys.executable,
                            "-u",
                            "-m",
                            "pip",
                            "install",
                            "--upgrade",
                        ]
                        + app.requires,
                        check=True,
                    )
                except subprocess.CalledProcessError as e:
                    raise DependencyInstallError() from e
        else:
            self.logger.info("No application dependencies.")

    def run_dev_app(self, app: BaseConfig, env: dict, **options):
        """Run the app in the dev environment.

        :param app: The config object for the app
        :param env: environment dictionary for sub command
        """
        try:
            # Invoke the app.
            self.tools.subprocess.run(
                [
                    sys.executable,
                    "-u",
                    "-c",
                    (
                        "import runpy, sys;"
                        "sys.path.pop(0);"
                        f'runpy.run_module("{app.module_name}", run_name="__main__", alter_sys=True)'
                    ),
                ],
                env=env,
                check=True,
                cwd=self.tools.home_path,
                stream_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Unable to start application '{app.app_name}'"
            ) from e

    def get_environment(self, app):
        # Create a shell environment where PYTHONPATH points to the source
        # directories described by the app config.
        return {
            "PYTHONPATH": os.pathsep.join(
                os.fsdecode(Path.cwd() / path) for path in app.PYTHONPATH
            )
        }

    def __call__(
        self,
        appname: Optional[str] = None,
        update_dependencies: Optional[bool] = False,
        run_app: Optional[bool] = True,
        **options,
    ):
        # Confirm all required tools are available
        self.verify_tools()

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

        self.verify_app_tools(app)

        # Look for the existence of a dist-info file.
        # If one exists, assume that the dependencies have already been
        # installed. If a dependency update has been manually requested,
        # do it regardless.
        dist_info_path = (
            self.app_module_path(app).parent / f"{app.module_name}.dist-info"
        )
        if not run_app:
            # If we are not running the app, it means we should update dependencies.
            update_dependencies = True
        if update_dependencies or not dist_info_path.exists():
            self.logger.info("Installing dependencies...", prefix=app.app_name)
            self.install_dev_dependencies(app, **options)
            write_dist_info(app, dist_info_path)

        if run_app:
            self.logger.info("Starting in dev mode...", prefix=app.app_name)
            env = self.get_environment(app)
            return self.run_dev_app(app, env, **options)
