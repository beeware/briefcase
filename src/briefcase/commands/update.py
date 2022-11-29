from typing import Optional

from briefcase.config import BaseConfig

from .base import full_options
from .create import CreateCommand


class UpdateCommand(CreateCommand):
    command = "update"

    def add_options(self, parser):
        parser.add_argument(
            "-r",
            "--update-requirements",
            action="store_true",
            help="Update requirements for the app",
        )
        parser.add_argument(
            "--update-resources",
            action="store_true",
            help="Update app resources (icons, splash screens, etc)",
        )

        parser.add_argument(
            "--test",
            dest="test_mode",
            action="store_true",
            help="Update the app in test mode",
        )

    def update_app(
        self,
        app: BaseConfig,
        update: Optional[bool],
        update_requirements: Optional[bool],
        update_resources: Optional[bool],
        test_mode: Optional[bool],
        **options,
    ):
        """Update an existing application bundle.

        :param app: The config object for the app
        :param update: Should the app be updated?
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

        if update or (test_mode and update is None):
            self.logger.info("Updating application code...", prefix=app.app_name)
            self.install_app_code(app=app, test_mode=test_mode)

        if update_requirements or (test_mode and update_requirements is None):
            self.logger.info("Updating requirements...", prefix=app.app_name)
            self.install_app_requirements(app=app, test_mode=test_mode)

        if update_resources or (test_mode and update_resources is None):
            self.logger.info(
                "Updating extra application resources...", prefix=app.app_name
            )
            self.install_app_resources(app=app)

        self.logger.info("Removing unneeded app content...", prefix=app.app_name)
        self.cleanup_app_content(app=app)

        self.logger.info("Application updated.", prefix=app.app_name)

    def __call__(
        self,
        app: Optional[BaseConfig] = None,
        update: bool = True,
        update_requirements: bool = False,
        update_resources: bool = False,
        test_mode: bool = False,
        **options,
    ):
        # Confirm all required tools are available
        self.verify_tools()

        if app:
            state = self.update_app(
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
                state = self.update_app(
                    app,
                    update=update,
                    update_requirements=update_requirements,
                    update_resources=update_resources,
                    test_mode=test_mode,
                    **full_options(state, options),
                )

        return state
