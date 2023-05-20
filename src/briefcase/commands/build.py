from typing import Optional

from packaging.version import Version

import briefcase
from briefcase.config import AppConfig, BaseConfig
from briefcase.exceptions import BriefcaseCommandError

from .base import BaseCommand, full_options


class BuildCommand(BaseCommand):
    command = "build"
    description = "Build an app for a target platform."

    def add_options(self, parser):
        self._add_update_options(parser, context_label=" before building")
        self._add_test_options(parser, context_label="Build")

    def build_app(self, app: AppConfig, **options):
        """Build an application.

        :param app: The application to build
        """
        # Default implementation; nothing to build.

    def verify_template(self, app: AppConfig):
        """Verify the template satisfies the Command's requirements."""
        self.logger.info("Checking template compatability...", prefix=app.app_name)

        with self.input.wait_bar("Verifying Briefcase support..."):
            # check against the "release" for each Version since versions
            # such as "0.3.15.dev123" are considered older than "0.3.15"

            if template_target := self.briefcase_target_version(app=app):
                template_target = Version(template_target).release

            if platform_target := self.oldest_compatible_briefcase:
                platform_target = Version(platform_target).release

            if platform_target and not template_target:
                raise BriefcaseCommandError(
                    f"""\
The app template must declare a target version of Briefcase to confirm it is
compatible with this version of Briefcase.

The template's target Briefcase version must be {'.'.join(map(str, platform_target))} or later.

Once the template is updated, run the create command:

    $ briefcase create {self.platform} {self.output_format}
"""
                )

            current_version = Version(briefcase.__version__).release
            if (platform_target and platform_target > template_target) or (
                template_target and template_target > current_version
            ):
                minimum_version = ".".join(map(str, platform_target or current_version))
                raise BriefcaseCommandError(
                    f"""\
The app template is not compatible with this version of Briefcase since it is
targeting version {'.'.join(map(str, template_target))}.

If you are using BeeWare's default template, then running the create command
to update the app using a compatible version of the app template.

If a custom template is being used, it must be updated to be compatible with
Briefcase version {minimum_version} before re-running the create command.

To run the create command:

    $ briefcase create {self.platform} {self.output_format}
"""
                )

    def _build_app(
        self,
        app: AppConfig,
        update: bool,
        update_requirements: bool,
        update_resources: bool,
        update_support: bool,
        no_update: bool,
        test_mode: bool,
        **options,
    ):
        """Internal method to invoke a build on a single app. Ensures the app exists,
        and has been updated (if requested) before attempting to issue the actual build
        command.

        :param app: The application to build
        :param update: Should the application be updated before building?
        :param update_requirements: Should the application requirements be
            updated before building?
        :param update_resources: Should the application resources be updated
            before building?
        :param update_support: Should the application support be updated?
        :param no_update: Should automated updates be disabled?
        :param test_mode: Is the app being build in test mode?
        """
        if not self.bundle_path(app).exists():
            state = self.create_command(app, test_mode=test_mode, **options)
        elif (
            update  # An explicit update has been requested
            or update_requirements  # An explicit update of requirements has been requested
            or update_resources  # An explicit update of resources has been requested
            or update_support  # An explicit update of app support has been requested
            or (
                test_mode and not no_update
            )  # Test mode, but updates have not been disabled
        ):
            state = self.update_command(
                app,
                update_requirements=update_requirements,
                update_resources=update_resources,
                update_support=update_support,
                test_mode=test_mode,
                **options,
            )
        else:
            state = None

        self.verify_template(app)
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
        update: bool = False,
        update_requirements: bool = False,
        update_resources: bool = False,
        update_support: bool = False,
        no_update: bool = False,
        test_mode: bool = False,
        **options,
    ):
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

        # Confirm host compatibility, that all required tools are available,
        # and that the app configuration is finalized.
        self.finalize(app)

        if app:
            state = self._build_app(
                app,
                update=update,
                update_requirements=update_requirements,
                update_resources=update_resources,
                update_support=update_support,
                no_update=no_update,
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
                    update_support=update_support,
                    no_update=no_update,
                    test_mode=test_mode,
                    **full_options(state, options),
                )

        return state
