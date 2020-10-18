import subprocess
import sys
from typing import Optional

from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError

from .base import BaseCommand
from .create import DependencyInstallError, write_dist_info


class InstallCommand(BaseCommand):
    cmd_line = 'briefcase install'
    command = 'install'
    output_format = None
    description = 'Install briefcase project dependencies.'

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
            '--update',
            action="store_true",
            help='Update dependencies for app'
        )

    def install_dev_dependencies(
            self, app: BaseConfig, update: bool, **options
    ):
        """
        Install the dependencies for the app devly.

        :param app: The config object for the app
        :param update: should or should not update dependencies if exists
        """
        # Look for the existence of a dist-info file.
        # If one exists, assume that the dependencies have already been
        # installed. If a dependency update has been manually requested,
        # do it regardless.
        dist_info_path = (
            self.app_module_path(app).parent
            / '{app.module_name}.dist-info'.format(app=app)
        )
        if not update and dist_info_path.exists():
            return
        print()
        print('[{app.app_name}] Installing dependencies...'.format(
            app=app
        ))
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
        write_dist_info(app, dist_info_path)

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

    def get_app(self, appname):
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
        return app
