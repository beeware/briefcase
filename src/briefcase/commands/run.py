from .base import BaseCommand


class RunCommand(BaseCommand):
    # requires build
    # causes update && build on flag

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
            help='Update the payload of the app be updated before execution'
        )

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

        target_file = self.target(app)
        if not target_file.exists():
            self.create(app)
        elif self.options.update:
            self.update(app)

        print("RUN:", self.description)
