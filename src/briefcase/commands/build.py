from typing import Optional

from briefcase.config import BaseConfig

from .base import BaseCommand


class BuildCommand(BaseCommand):
    def add_options(self, parser):
        parser.add_argument(
            '-u',
            '--update',
            action="store_true",
            help='Update the app before building'
        )

    def build_app(self, app: BaseConfig):
        """
        Build an application.

        :param app: The application to build
        """
        # Default implementation; nothing to build.

    def build_single_app(self, app: BaseConfig):
        """
        Internal method to invoke a build on a single app.
        Ensures the app exists, and has been updated (if requested)

        :param app: The application to build
        """
        target_file = self.bundle_path(app)
        if not target_file.exists():
            self.create_command(app)
        elif self.options.update:
            self.update_command(app)

        self.build_app(app)

    def __call__(self, app: Optional[BaseConfig] = None):
        self.verify_tools()

        if app:
            self.build_single_app(app)
        else:
            for app_name, app in self.apps.items():
                self.build_single_app(app)
