import os
import subprocess
import sys
from typing import Optional

from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError

from .base import BaseCommand
from .create import DependencyInstallError, write_dist_info


class DevCommand(BaseCommand):
    cmd_line = 'briefcase dev'
    command = 'dev'
    output_format = None
    description = 'Run a briefcase project in the dev environment'

    @property
    def platform(self):
        """The dev command always reports as the local platform."""
        return {
            'darwin': 'macOS',
            'linux': 'linux',
            'win32': 'windows',
        }[sys.platform]

    def bundle_path(self, app):
        "A placeholder; Dev command doesn't have a bundle path"
        raise NotImplementedError()

    def binary_path(self, app):
        "A placeholder; Dev command doesn't have a binary path"
        raise NotImplementedError()

    def distribution_path(self, app):
        "A placeholder; Dev command doesn't have a distribution path"
        raise NotImplementedError()

    def add_options(self, parser):
        parser.add_argument(
            '-a',
            '--app',
            dest='appname',
            help='The app to run'
        )
        parser.add_argument(
            '-d',
            '--update-dependencies',
            action="store_true",
            help='Update dependencies for app'
        )

    def install_dev_dependencies(self, app: BaseConfig, **kwargs):
        """
        Install the dependencies for the app devly.

        :param app: The config object for the app
        """
        if app.requires:
            try:
                self.subprocess.run(
                    [
                        sys.executable, "-m",
                        "pip", "install",
                        "--upgrade",
                    ] + app.requires,
                    check=True,
                )
            except subprocess.CalledProcessError:
                raise DependencyInstallError()
        else:
            print("No application dependencies.")

    def run_dev_app(self, app: BaseConfig, env: dict, **kwargs):
        """
        Run the app in the dev environment.

        :param app: The config object for the app
        :param env: environment dictionary for sub command
        """
        try:
            # Invoke the app.
            self.subprocess.run(
                [sys.executable, "-m", app.module_name],
                env=env,
                check=True,
            )
        except subprocess.CalledProcessError:
            print()
            raise BriefcaseCommandError(
                "Unable to start application '{app.app_name}'".format(
                    app=app
                ))

    def get_environment(self, app):
        # Create a shell environment where PYTHONPATH points to the source
        # directories described by the app config.
        env = os.environ.copy()
        paths = []
        for app in app.sources:
            path = app.rsplit('/', 1)[0]
            if path not in paths:
                paths.append(path)

        env['PYTHONPATH'] = os.pathsep.join(paths)
        return env

    def __call__(
        self,
        appname: Optional[str] = None,
        update_dependencies: Optional[bool] = False,
        **kwargs
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
            except KeyError:
                raise BriefcaseCommandError(
                    "Project doesn't define an application named '{appname}'".format(
                        appname=appname
                    ))
        else:
            raise BriefcaseCommandError(
                "Project specifies more than one application; "
                "use --app to specify which one to start."
            )

        # Look for the existence of a dist-info file.
        # If one exists, assume that the dependencies have already been
        # installed. If a dependency update has been manually requested,
        # do it regardless.
        dist_info_path = self.app_module_path(app).parent / '{app.module_name}.dist-info'.format(app=app)
        if update_dependencies or not dist_info_path.exists():
            print()
            print('[{app.app_name}] Installing dependencies...'.format(
                app=app
            ))
            self.install_dev_dependencies(app, **kwargs)
            write_dist_info(app, dist_info_path)

        print()
        print('[{app.app_name}] Starting in dev mode...'.format(
            app=app
        ))
        env = self.get_environment(app)
        state = self.run_dev_app(app, env, **kwargs)
        return state
