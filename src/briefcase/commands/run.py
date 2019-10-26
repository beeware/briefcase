from abc import abstractmethod

from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError

from .base import BaseCommand


class RunCommand(BaseCommand):
    def add_options(self, parser):
        parser.add_argument(
            '-a',
            '--app',
            help='The app to run'
        )
        parser.add_argument(
            '-u',
            '--update',
            action="store_true",
            help='Update the app before execution'
        )

    @abstractmethod
    def run_app(self, app: BaseConfig):
        """
        Start an application.

        :param app: The application to start
        """
        ...

    def __call__(self):
        # Which app should we run? If there's only one defined
        # in pyproject.toml, then we can use it as a default;
        # otherwise look for a -a/--app option.
        if len(self.apps) == 1:
            app = list(self.apps.values())[0]
        elif self.options.app:
            try:
                app = self.apps[self.options.app]
            except KeyError:
                raise BriefcaseCommandError(
                    "Project doesn't define an application named '{appname}'".format(
                        appname=self.options.app
                    ))
        else:
            raise BriefcaseCommandError(
                "Project specifies more than one application; "
                "use --app to specify which one to start."
            )

        target_file = self.binary_path(app)
        if not target_file.exists():
            self.create_command(app)
            self.build_command(app)
        elif self.options.update:
            self.update_command(app)
            self.build_command(app)

        self.run_app(app)
