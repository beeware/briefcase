from __future__ import annotations

from contextlib import suppress

from briefcase.config import AppConfig
from briefcase.exceptions import MissingSupportPackage

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
        update_app: bool,
        update_requirements: bool,
        update_resources: bool,
        update_support: bool,
        update_stub: bool,
        test_mode: bool,
        **options,
    ) -> dict:
        """Update an existing application bundle.

        :param app: The config object for the app
        :param update_app: Should the app sources be updated?
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
            return {}

        if not update_app:
            update_app = self.tracking_is_source_modified(
                app, sources=app.sources(test_mode=test_mode)
            )
            if update_app:  # TODO:PR: delete
                self.logger.warning("App source change detected")

        if not update_requirements:
            update_requirements = self.tracking_is_requirements_updated(
                app, requires=app.requires(test_mode=test_mode)
            )
            if update_requirements:  # TODO:PR: delete
                self.logger.warning("Requirements change detected")

        if not update_resources:
            update_resources = self.tracking_is_resources_updated(
                app,
                resources=self._resolve_app_resources(app, do_install=False).values(),
            )
            if update_resources:  # TODO:PR: delete
                self.logger.warning("Resources change detected")

        if not update_support:
            # an app's missing support package will be reported later
            with suppress(MissingSupportPackage):
                update_support = self.tracking_is_support_package_updated(
                    app, support_url=self._app_support_package(app, warn_user=False)[1]
                )
            if update_support:  # TODO:PR: delete
                self.logger.warning("Support package change detected")

        if not update_stub:
            # TODO:PR: figure out a better way to protect against no binary revision
            try:
                self.stub_binary_revision(app)
            except KeyError:
                pass
            else:
                update_stub = self.tracking_is_stub_binary_updated(
                    app, stub_url=self._stub_binary(app, warn_user=False)[1]
                )
            if update_stub:  # TODO:PR: delete
                self.logger.warning("Binary stub change detected")

        if is_app_being_updated := (
            update_app
            or update_requirements
            or update_resources
            or update_support
            or update_stub
        ):
            self.verify_app(app)

        if update_app:
            self.logger.info("Updating application code...", prefix=app.app_name)
            self.install_app_code(app, test_mode=test_mode)

        if update_requirements:
            self.logger.info("Updating requirements...", prefix=app.app_name)
            self.install_app_requirements(app, test_mode=test_mode)

        if update_resources:
            self.logger.info("Updating application resources...", prefix=app.app_name)
            self.install_app_resources(app)

        if update_support:
            self.logger.info("Updating application support...", prefix=app.app_name)
            self.cleanup_app_support_package(app)
            self.install_app_support_package(app)

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
                self.cleanup_stub_binary(app)
                self.install_stub_binary(app)

        self.logger.info("Removing unneeded app content...", prefix=app.app_name)
        self.cleanup_app_content(app)

        if is_app_being_updated:
            self.logger.info("Removing unneeded app content...", prefix=app.app_name)
            self.cleanup_app_content(app)

            self.logger.info("Application updated.", prefix=app.app_name)

        return {
            "is_app_source_updated": update_app,
            "is_requirements_updated": update_requirements,
            "is_resources_updated": update_resources,
            "is_support_package_updated": update_support,
            "is_binary_stub_updated": update_stub,
            "is_app_updated": is_app_being_updated,
        }

    def __call__(
        self,
        app: AppConfig | None = None,
        update_app: bool = True,
        update_requirements: bool = False,
        update_resources: bool = False,
        update_support: bool = False,
        update_stub: bool = False,
        test_mode: bool = False,
        **options,
    ) -> dict:
        # Finish preparing the AppConfigs and run final checks required to for command
        self.finalize(app)

        if app:
            state = self.update_app(
                app,
                update_app=update_app,
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
                    update_app=update_app,
                    update_requirements=update_requirements,
                    update_resources=update_resources,
                    update_support=update_support,
                    update_stub=update_stub,
                    test_mode=test_mode,
                    **full_options(state, options),
                )

        return state
