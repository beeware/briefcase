from abc import abstractmethod
from typing import Optional

from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError

from .base import BaseCommand, full_options


class RunCommand(BaseCommand):
    command = 'run'

    def add_options(self, parser):
        parser.add_argument(
            '-a',
            '--app',
            dest='appname',
            help='The app to run'
        )
        parser.add_argument(
            '-u',
            '--update',
            action="store_true",
            help='Update the app before execution'
        )

    @abstractmethod
    def run_app(self, app: BaseConfig, **options):
        """
        Start an application.

        :param app: The application to start
        """
        ...

    def __call__(
        self,
        appname: Optional[str] = None,
        update: Optional[bool] = False,
        **options
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

        template_file = self.bundle_path(app)
        binary_file = self.binary_path(app)
        if not template_file.exists():
            state = self.create_command(app, **options)
            state = self.build_command(app, **full_options(state, options))
        elif update:
            state = self.update_command(app, **options)
            state = self.build_command(app, **full_options(state, options))
        elif not binary_file.exists():
            state = self.build_command(app, **options)
        else:
            state = None

        state = self.run_app(app, **full_options(state, options))

        return state
