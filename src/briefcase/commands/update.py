from __future__ import annotations

import argparse

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError

from .base import full_options
from .create import CreateCommand


class UpdateCommand(CreateCommand):
    command = "update"
    description = "Update the source, dependencies, and resources for an app."

    def add_options(self, parser):
        self._add_update_options(parser, update=False)
        self._add_test_options(parser, context_label="Update")

        parser.add_argument(
            "-a",
            "--app",
            dest="app_name",
            help="Name of the app to update (if multiple apps exist in the project)",
            default=argparse.SUPPRESS,
        )

    def update_app(
        self,
        app: AppConfig,
        update_requirements: bool,
        update_resources: bool,
        update_support: bool,
        update_stub: bool,
        **options,
    ) -> dict | None:
        """Update an existing application bundle.

        :param app: The config object for the app
        :param update_requirements: Should requirements be updated?
        :param update_resources: Should extra resources be updated?
        :param update_support: Should app support be updated?
        :param update_stub: Should stub binary be updated?
        """

        if app.external_package_path:
            raise BriefcaseCommandError(
                f"{app.app_name!r} is declared as an external app. External apps "
                "(apps defining 'external_package_path') cannot be updated."
            )

        if not self.bundle_path(app).exists():
            self.console.error(
                "Application does not exist; call create first!", prefix=app.app_name
            )
            return

        self.verify_app(app)

        self.console.info("Updating application code...", prefix=app.app_name)
        self.install_app_code(app=app)

        if update_requirements:
            self.console.info("Updating requirements...", prefix=app.app_name)
            self.install_app_requirements(app=app)

        if update_resources:
            self.console.info("Updating application resources...", prefix=app.app_name)
            self.install_app_resources(app=app)

        if update_support:
            self.console.info("Updating application support...", prefix=app.app_name)
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
                self.console.info("Updating stub binary...", prefix=app.app_name)
                self.cleanup_stub_binary(app=app)
                self.install_stub_binary(app=app)

        self.console.info("Removing unneeded app content...", prefix=app.app_name)
        self.cleanup_app_content(app=app)

        self.console.info("Application updated.", prefix=app.app_name)

    def __call__(
        self,
        app: AppConfig | None = None,
        app_name: str | None = None,
        update_requirements: bool = False,
        update_resources: bool = False,
        update_support: bool = False,
        update_stub: bool = False,
        test_mode: bool = False,
        **options,
    ) -> dict | None:
        # Confirm host compatibility, that all required tools are available,
        # and that the app configuration is finalized.
        self.finalize(app, test_mode)

        if app_name:
            try:
                apps_to_update = {app_name: self.apps[app_name]}
            except KeyError:
                raise BriefcaseCommandError(
                    f"App '{app_name}' does not exist in this project."
                )
        elif app:
            apps_to_update = {app.app_name: app}
        else:
            apps_to_update = self.apps

        state = None
        for _, app_obj in sorted(apps_to_update.items()):
            state = self.update_app(
                app_obj,
                update_requirements=update_requirements,
                update_resources=update_resources,
                update_support=update_support,
                update_stub=update_stub,
                **full_options(state, options),
            )

        return state
