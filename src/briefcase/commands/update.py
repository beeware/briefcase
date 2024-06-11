from __future__ import annotations

from briefcase.config import AppConfig

from .base import full_options
from .create import CreateCommand


class UpdateCommand(CreateCommand):
    command = "update"
    description = "Update the source, dependencies, and resources for an app."

    def add_options(self, parser):
        self._add_update_options(parser, update=False)
        self._add_test_options(parser, context_label="Update")

    def update_app(
        self,
        app: AppConfig,
        update_requirements: bool,
        update_resources: bool,
        update_support: bool,
        update_stub: bool,
        test_mode: bool,
        **options,
    ) -> dict | None:
        """Update an existing application bundle.

        :param app: The config object for the app
        :param update_requirements: Should requirements be updated?
        :param update_resources: Should extra resources be updated?
        :param update_support: Should app support be updated?
        :param update_stub: Should stub binary be updated?
        :param test_mode: Should the app be updated in test mode?
        """

        if not self.bundle_path(app).exists():
            self.logger.error(
                "Application does not exist; call create first!", prefix=app.app_name
            )
            return

        self.verify_app(app)

        self.logger.info("Updating application code...", prefix=app.app_name)
        self.install_app_code(app=app, test_mode=test_mode)

        if update_requirements:
            self.logger.info("Updating requirements...", prefix=app.app_name)
            self.install_app_requirements(app=app, test_mode=test_mode)

        if update_resources:
            self.logger.info("Updating application resources...", prefix=app.app_name)
            self.install_app_resources(app=app)

        if update_support:
            self.logger.info("Updating application support...", prefix=app.app_name)
            self.cleanup_app_support_package(app=app)
            self.install_app_support_package(app=app)

        if update_stub:
            try:
                # If the platform uses a stub binary, the template will define a binary
                # revision. If this template configuration item doesn't exist, there's
                # no stub binary
                self.stub_binary_revision(app)
            except KeyError:
                pass
            else:
                self.logger.info("Updating stub binary...", prefix=app.app_name)
                self.cleanup_stub_binary(app=app)
                self.install_stub_binary(app=app)

        self.logger.info("Removing unneeded app content...", prefix=app.app_name)
        self.cleanup_app_content(app=app)

        self.logger.info("Application updated.", prefix=app.app_name)

    def __call__(
        self,
        app: AppConfig | None = None,
        update_requirements: bool = False,
        update_resources: bool = False,
        update_support: bool = False,
        update_stub: bool = False,
        test_mode: bool = False,
        **options,
    ) -> dict | None:
        # Confirm host compatibility, that all required tools are available,
        # and that the app configuration is finalized.
        self.finalize(app)

        if app:
            state = self.update_app(
                app,
                update_requirements=update_requirements,
                update_resources=update_resources,
                update_support=update_support,
                update_stub=update_stub,
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
                    update_support=update_support,
                    update_stub=update_stub,
                    test_mode=test_mode,
                    **full_options(state, options),
                )

        return state
