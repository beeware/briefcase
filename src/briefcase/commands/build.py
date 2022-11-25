from typing import Optional

from briefcase.config import BaseConfig

from .base import BaseCommand, full_options


class BuildCommand(BaseCommand):
    command = "build"

    def add_options(self, parser):
        # Update is a tri-valued argument; it can be specified as --update
        # or --no-update, with a default value of None. In the presence of
        # the default, there is different behavior depending on whether
        # we are in test mode.
        parser.add_argument(
            "-u",
            "--update",
            action="store_const",
            const=True,
            help="Update the app before building",
        )
        parser.add_argument(
            "--no-update",
            dest="update",
            action="store_const",
            const=False,
            help="Prevent any automated update before building.",
        )
        parser.add_argument(
            "--test",
            dest="test_mode",
            action="store_true",
            help="Build the app in test mode",
        )

    def build_app(self, app: BaseConfig, **options):
        """Build an application.

        :param app: The application to build
        """
        # Default implementation; nothing to build.

    def _build_app(
        self,
        app: BaseConfig,
        update: Optional[bool],
        test_mode: bool,
        **options,
    ):
        """Internal method to invoke a build on a single app. Ensures the app
        exists, and has been updated (if requested) before attempting to issue
        the actual build command.

        :param app: The application to build?
        :param update: Should the application be updated first?
        :param test_mode: Is the app being build in test mode?
        """
        target_file = self.bundle_path(app)
        if not target_file.exists():
            state = self.create_command(app, test_mode=test_mode, **options)
        elif update or (test_mode and update is None):
            state = self.update_command(app, test_mode=test_mode, **options)
        else:
            state = None

        self.verify_app_tools(app)

        state = self.build_app(app, test_mode=test_mode, **full_options(state, options))

        qualifier = " (test mode)" if test_mode else ""
        self.logger.info(
            f"Built {self.binary_path(app).relative_to(self.base_path)}{qualifier}",
            prefix=app.app_name,
        )
        return state

    def __call__(
        self,
        app: Optional[BaseConfig] = None,
        update: Optional[bool] = None,
        test_mode: bool = False,
        **options,
    ):
        # Confirm all required tools are available
        self.verify_tools()

        if app:
            state = self._build_app(app, update=update, test_mode=test_mode, **options)
        else:
            state = None
            for app_name, app in sorted(self.apps.items()):
                state = self._build_app(
                    app,
                    update=update,
                    test_mode=test_mode,
                    **full_options(state, options),
                )

        return state
