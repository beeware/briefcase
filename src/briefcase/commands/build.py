from typing import Optional

from briefcase.config import BaseConfig

from .base import BaseCommand, full_options


class BuildCommand(BaseCommand):
    command = 'build'

    def add_options(self, parser):
        parser.add_argument(
            '-u',
            '--update',
            action="store_true",
            help='Update the app before building'
        )

    def build_app(self, app: BaseConfig, **options):
        """
        Build an application.

        :param app: The application to build
        """
        # Default implementation; nothing to build.

    def _build_app(self, app: BaseConfig, update: bool, **options):
        """
        Internal method to invoke a build on a single app.
        Ensures the app exists, and has been updated (if requested) before
        attempting to issue the actual build command.

        :param app: The application to build?
        :param update: Should the application be updated first?
        """
        target_file = self.bundle_path(app)
        if not target_file.exists():
            state = self.create_command(app, **options)
        elif update:
            state = self.update_command(app, **options)
        else:
            state = None

        state = self.build_app(app, **full_options(state, options))

        print()
        print("[{app.app_name}] Built {filename}".format(
            app=app,
            filename=self.binary_path(app).relative_to(self.base_path),
        ))
        return state

    def __call__(
        self,
        app: Optional[BaseConfig] = None,
        update: bool = False,
        **options
    ):
        # Confirm all required tools are available
        self.verify_tools()

        if app:
            state = self._build_app(app, update=update, **options)
        else:
            state = None
            for app_name, app in sorted(self.apps.items()):
                state = self._build_app(app, update=update, **full_options(state, options))

        return state
