import os
import subprocess
import sys
from typing import Optional

from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError

from .install import InstallCommand


class DevCommand(InstallCommand):
    cmd_line = 'briefcase dev'
    command = 'dev'
    output_format = None
    description = 'Run a briefcase project in the dev environment'

    def run_dev_app(self, app: BaseConfig, env: dict, **options):
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
        env['PYTHONPATH'] = os.pathsep.join(app.PYTHONPATH)
        return env

    def __call__(
        self,
        appname: Optional[str] = None,
        update: Optional[bool] = False,
        **options
    ):
        # Confirm all required tools are available
        self.verify_tools()
        app = self.get_app(appname)
        self.install_dev_dependencies(app, update, **options)

        print()
        print('[{app.app_name}] Starting in dev mode...'.format(
            app=app
        ))
        env = self.get_environment(app)
        state = self.run_dev_app(app, env, **options)
        return state
