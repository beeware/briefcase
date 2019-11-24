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

    def _build_app(self, app: BaseConfig):
        """
        Internal method to invoke a build on a single app.
        Ensures the app exists, and has been updated (if requested) before
        attempting to issue the actual build command.

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
            self._build_app(app)
        else:
            for app_name, app in sorted(self.apps.items()):
                self._build_app(app)
