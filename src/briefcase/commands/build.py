from typing import Optional

from briefcase.config import BaseConfig

from .base import BaseCommand, full_kwargs


class BuildCommand(BaseCommand):
    command = 'build'

    def add_options(self, parser):
        parser.add_argument(
            '-u',
            '--update',
            action="store_true",
            help='Update the app before building'
        )

    def build_app(self, app: BaseConfig, **kwargs):
        """
        Build an application.

        :param app: The application to build
        """
        # Default implementation; nothing to build.

    def _build_app(self, app: BaseConfig, update: bool, **kwargs):
        """
        Internal method to invoke a build on a single app.
        Ensures the app exists, and has been updated (if requested) before
        attempting to issue the actual build command.

        :param app: The application to build?
        :param update: Should the application be updated first?
        """
        target_file = self.bundle_path(app)
        if not target_file.exists():
            state = self.create_command(app, **kwargs)
        elif update:
            state = self.update_command(app, **kwargs)
        else:
            state = None

        state = self.build_app(app, **full_kwargs(state, kwargs))

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
        **kwargs
    ):
        # Confirm all required tools are available
        self.verify_tools()

        if app:
            state = self._build_app(app, update=update, **kwargs)
        else:
            state = None
            for app_name, app in sorted(self.apps.items()):
                state = self._build_app(app, update=update, **full_kwargs(state, kwargs))

        return state
