from typing import Optional

from briefcase.config import BaseConfig

from .base import BaseCommand, full_options


class BuildCommand(BaseCommand):
    command = "build"

    def add_options(self, parser):
        self._add_update_options(parser, context_label=" before building")
        self._add_test_options(parser, context_label="Build")

    def build_app(self, app: BaseConfig, **options):
        """Build an application.

        :param app: The application to build
        """
        # Default implementation; nothing to build.

    def _build_app(
        self,
        app: BaseConfig,
        update: Optional[bool],
        update_requirements: Optional[bool],
        update_resources: Optional[bool],
        test_mode: bool,
        **options,
    ):
        """Internal method to invoke a build on a single app. Ensures the app
        exists, and has been updated (if requested) before attempting to issue
        the actual build command.

        :param app: The application to build
        :param update: Should the application be updated before building?
        :param update_requirements: Should the application requirements be
            updated before building?
        :param update_resources: Should the application resources be updated
            before building?
        :param test_mode: Is the app being build in test mode?
        """
        target_file = self.bundle_path(app)
        if not target_file.exists():
            state = self.create_command(app, test_mode=test_mode, **options)
        elif (
            update  # An explicit update has been requested
            or update_requirements  # An explicit update of requirements has been requested
            or update_resources  # An explicit update of resources has been requested
            or (
                test_mode
                and (
                    update is None
                    or update_requirements is None
                    or update_resources is None
                )
            )  # Test mode, but updates have not been completely disabled
        ):
            state = self.update_command(
                app,
                update=update,
                update_requirements=update_requirements,
                update_resources=update_resources,
                test_mode=test_mode,
                **options,
            )
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
        update_requirements: Optional[bool] = None,
        update_resources: Optional[bool] = None,
        test_mode: bool = False,
        **options,
    ):
        # Confirm all required tools are available
        self.verify_tools()

        if app:
            state = self._build_app(
                app,
                update=update,
                update_requirements=update_requirements,
                update_resources=update_resources,
                test_mode=test_mode,
                **options,
            )
        else:
            state = None
            for app_name, app in sorted(self.apps.items()):
                state = self._build_app(
                    app,
                    update=update,
                    update_requirements=update_requirements,
                    update_resources=update_resources,
                    test_mode=test_mode,
                    **full_options(state, options),
                )

        return state
