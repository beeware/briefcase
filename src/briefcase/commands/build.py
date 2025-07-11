from __future__ import annotations

import argparse

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError

from .base import BaseCommand, full_options


class BuildCommand(BaseCommand):
    command = "build"
    description = "Build an app for a target platform."

    def add_options(self, parser):
        self._add_update_options(parser, context_label=" before building")
        self._add_test_options(parser, context_label="Build")

        parser.add_argument(
            "-a",
            "--app",
            dest="app_name",
            help="Name of the app to build (if multiple apps exist in the project)",
            default=argparse.SUPPRESS,
        )

    def build_app(self, app: AppConfig, **options):
        """Build an application.

        :param app: The application to build
        """
        # Default implementation; nothing to build.

    def _build_app(
        self,
        app: AppConfig,
        update: bool,
        update_requirements: bool,
        update_resources: bool,
        update_support: bool,
        update_stub: bool,
        no_update: bool,
        **options,
    ) -> dict | None:
        """Internal method to invoke a build on a single app. Ensures the app exists,
        and has been updated (if requested) before attempting to issue the actual build
        command.

        :param app: The application to build
        :param update: Should the application be updated before building?
        :param update_requirements: Should the application requirements be updated
            before building?
        :param update_resources: Should the application resources be updated before
            building?
        :param update_support: Should the application support be updated?
        :param update_stub: Should the stub binary be updated?
        :param no_update: Should automated updates be disabled?
        """
        if app.external_package_path:
            raise BriefcaseCommandError(
                f"{app.app_name!r} is declared as an external app. External apps "
                "(apps defining 'external_package_path') cannot be built."
            )

        if not self.bundle_path(app).exists():
            state = self.create_command(app, **options)
        elif (
            update  # An explicit update has been requested
            or update_requirements  # An explicit update of requirements has been requested
            or update_resources  # An explicit update of resources has been requested
            or update_support  # An explicit update of app support has been requested
            or update_stub  # An explicit update of the stub binary has been requested
            or (
                app.test_mode and not no_update
            )  # Test mode, but updates have not been disabled
        ):
            state = self.update_command(
                app,
                update_requirements=update_requirements,
                update_resources=update_resources,
                update_support=update_support,
                update_stub=update_stub,
                **options,
            )
        else:
            state = None

        self.verify_app(app)

        state = self.build_app(app, **full_options(state, options))

        qualifier = " (test mode)" if app.test_mode else ""
        self.console.info(
            f"Built {self.binary_path(app).relative_to(self.base_path)}{qualifier}",
            prefix=app.app_name,
        )
        return state

    def __call__(
        self,
        app: AppConfig | None = None,
        app_name: str | None = None,
        update: bool = False,
        update_requirements: bool = False,
        update_resources: bool = False,
        update_support: bool = False,
        update_stub: bool = False,
        no_update: bool = False,
        test_mode: bool = False,
        **options,
    ) -> dict | None:
        # Has the user requested an invalid set of options?
        # This can't be done with argparse, because it isn't a simple mutually exclusive group.
        if no_update:
            if update:
                raise BriefcaseCommandError(
                    "Cannot specify both --update and --no-update"
                )
            if update_requirements:
                raise BriefcaseCommandError(
                    "Cannot specify both --update-requirements and --no-update"
                )
            if update_resources:
                raise BriefcaseCommandError(
                    "Cannot specify both --update-resources and --no-update"
                )
            if update_support:
                raise BriefcaseCommandError(
                    "Cannot specify both --update-support and --no-update"
                )
            if update_stub:
                raise BriefcaseCommandError(
                    "Cannot specify both --update-stub and --no-update"
                )

        # Confirm host compatibility, that all required tools are available,
        # and that the app configuration is finalized.
        self.finalize(app, test_mode)

        if app_name:
            try:
                apps_to_build = {app_name: self.apps[app_name]}
            except KeyError:
                raise BriefcaseCommandError(
                    f"App '{app_name}' does not exist in this project."
                )
        elif app:
            apps_to_build = {app.app_name: app}
        else:
            apps_to_build = self.apps

        state = None
        for _, app_obj in sorted(apps_to_build.items()):
            state = self._build_app(
                app_obj,
                update=update,
                update_requirements=update_requirements,
                update_resources=update_resources,
                update_support=update_support,
                update_stub=update_stub,
                no_update=no_update,
                **full_options(state, options),
            )

        return state
