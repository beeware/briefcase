from __future__ import annotations

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError

from .base import BaseCommand, full_options


class BuildCommand(BaseCommand):
    command = "build"
    description = "Build an app for a target platform."

    def add_options(self, parser):
        self._add_update_options(parser, context_label=" before building")
        self._add_test_options(parser, context_label="Build")

    def build_app(self, app: AppConfig, test_mode: bool, **options):
        """Build an application.

        :param app: The application to build
        :param test_mode: Is the app being build in test mode?
        """
        # Default implementation; nothing to build.

    def check_for_recreate(self, app: AppConfig) -> bool:
        """Should the app be re-created because the environment changed?"""
        change_desc = ""

        if self.tracking_is_metadata_changed(app):
            change_desc = "Important project metadata"

        elif self.tracking_is_briefcase_version_updated(app):
            change_desc = "The version of Briefcase"

        elif self.tracking_is_python_env_updated(app):
            change_desc = "The version of Python"

        if change_desc != "":
            self.logger.info("Environment changes detected", prefix=app.app_name)
            self.logger.info(
                self.input.textwrap(
                    f"{change_desc} has changed since the app's bundle was originally "
                    f"created.\n"
                    "\n"
                    "It is recommended to re-create your app after this change. This "
                    "will overwrite any manual updates to the files in the app build "
                    "directory."
                )
            )
            self.input.prompt()
            return self.input.boolean_input("Would you like to do this now")
        else:
            return False

    def update_tracking(self, app: AppConfig, test_mode: bool):
        """Updates the tracking database for a successful build."""
        self.tracking_add_built_instant(app)
        # if an app build uses a requirements file, then the app's requirements are
        # updated during the build; therefore, a successful build means the requirements
        # were successfully reinstalled and need to be updated in the tracking database
        try:
            self.app_requirements_path(app)
        except KeyError:
            pass
        else:
            self.tracking_add_requirements(
                app, requires=app.requires(test_mode=test_mode)
            )

    def _build_app(
        self,
        app: AppConfig,
        build: bool,
        update: bool,
        update_requirements: bool,
        update_resources: bool,
        update_support: bool,
        update_stub: bool,
        no_update: bool,
        test_mode: bool,
        **options,
    ) -> dict:
        """Internal method to invoke a build on a single app. Ensures the app exists,
        and has been updated (if requested) before attempting to issue the actual build
        command.

        :param app: The application to build
        :param build: Should the application be built irrespective?
        :param update: Should the application be updated before building?
        :param update_requirements: Should the application requirements be updated
            before building?
        :param update_resources: Should the application resources be updated before
            building?
        :param update_support: Should the application support be updated?
        :param update_stub: Should the stub binary be updated?
        :param no_update: Should automated updates be disabled?
        :param test_mode: Is the app being build in test mode?
        """
        bundle_exists = self.bundle_path(app).exists()
        force_recreate = bundle_exists and self.check_for_recreate(app)

        if not bundle_exists or force_recreate:
            state = self.create_command(
                app,
                test_mode=test_mode,
                force=force_recreate,
                **options,
            )
            build = True  # always build after creating the app
        elif not no_update:
            state = self.update_command(
                app,
                update_app=update,
                update_requirements=update_requirements,
                update_resources=update_resources,
                update_support=update_support,
                update_stub=update_stub,
                test_mode=test_mode,
                **options,
            )
        else:
            state = {}

        if build or (state and state.pop("is_app_updated", False)):
            self.verify_app(app)

            state = self.build_app(
                app, test_mode=test_mode, **full_options(state, options)
            )
            self.update_tracking(app, test_mode=test_mode)

            qualifier = " (test mode)" if test_mode else ""
            self.logger.info(
                f"Built {self.binary_path(app).relative_to(self.base_path)}{qualifier}",
                prefix=app.app_name,
            )

        return state

    def __call__(
        self,
        app: AppConfig | None = None,
        build: bool = True,
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

        # Finish preparing the AppConfigs and run final checks required to for command
        self.finalize(app)

        if app:
            state = self._build_app(
                app,
                build=build,
                update=update,
                update_requirements=update_requirements,
                update_resources=update_resources,
                update_support=update_support,
                update_stub=update_stub,
                no_update=no_update,
                test_mode=test_mode,
                **options,
            )
        else:
            state = None
            for app_name, app in sorted(self.apps.items()):
                state = self._build_app(
                    app,
                    build=build,
                    update=update,
                    update_requirements=update_requirements,
                    update_resources=update_resources,
                    update_support=update_support,
                    update_stub=update_stub,
                    no_update=no_update,
                    test_mode=test_mode,
                    **full_options(state, options),
                )

        return state
