from typing import Optional

from briefcase.config import BaseConfig

from .base import full_options
from .create import CreateCommand


class UpdateCommand(CreateCommand):
    command = "update"
    description = "Update the source, dependencies, and resources for an app."

    def add_options(self, parser):
        self._add_update_options(
            parser,
            update=False,
        )
        self._add_test_options(parser, context_label="Update")

    def update_app(
        self,
        app: BaseConfig,
        update_requirements: bool,
        update_resources: bool,
        test_mode: bool,
        **options,
    ):
        """Update an existing application bundle.

        :param app: The config object for the app
        :param update_requirements: Should requirements be updated?
        :param update_resources: Should extra resources be updated?
        :param test_mode: Should the app be updated in test mode?
        """

        bundle_path = self.bundle_path(app)
        if not bundle_path.exists():
            self.logger.error(
                "Application does not exist; call create first!", prefix=app.app_name
            )
            return

        self.verify_app_tools(app)

        self.logger.info("Updating application code...", prefix=app.app_name)
        self.install_app_code(app=app, test_mode=test_mode)

        if update_requirements:
            self.logger.info("Updating requirements...", prefix=app.app_name)
            self.install_app_requirements(app=app, test_mode=test_mode)

        if update_resources:
            self.logger.info("Updating application resources...", prefix=app.app_name)
            self.install_app_resources(app=app)

        self.logger.info("Removing unneeded app content...", prefix=app.app_name)
        self.cleanup_app_content(app=app)

        self.logger.info("Application updated.", prefix=app.app_name)

    def __call__(
        self,
        app: Optional[BaseConfig] = None,
        update_requirements: bool = False,
        update_resources: bool = False,
        test_mode: bool = False,
        **options,
    ):
        # Confirm host compatibility, that all required tools are available,
        # and that the app configuration is finalized.
        self.finalize(app)

        if app:
            state = self.update_app(
                app,
                update_requirements=update_requirements,
                update_resources=update_resources,
                test_mode=test_mode,
                **options,
            )
        else:
            state = None
            for app_name, app in sorted(self.apps.items()):
                state = self.update_app(
                    app,
                    update_requirements=update_requirements,
                    update_resources=update_resources,
                    test_mode=test_mode,
                    **full_options(state, options),
                )

        return state
