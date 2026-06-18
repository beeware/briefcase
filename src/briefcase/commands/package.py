from __future__ import annotations

import argparse
from abc import abstractmethod

from briefcase.config import AppConfig, FinalizedAppConfig
from briefcase.exceptions import BriefcaseCommandError

from .base import BaseCommand, full_options


class PackageCommand(BaseCommand):
    command = "package"
    description = "Package an app for distribution."
    supports_external_packaging = False

    ADHOC_SIGN_HELP = "Ignored; signing is not supported"
    IDENTITY_HELP = "Ignored; signing is not supported"

    @property
    def packaging_formats(self):
        return [self.output_format]

    @property
    def default_packaging_format(self):
        return self.output_format

    @abstractmethod
    def distribution_path(self, app):
        """The path to the distributable artefact for the app.

        Requires that the packaging format has been annotated onto the application
        definition

        This is the single file that should be uploaded for distribution. This may be
        the binary (if the binary is a self-contained executable); however, if the
        output format produces an installer, it will be the path to the installer.

        :param app: The app config
        """

    def clean_dist_folder(self, app, **options):
        """Clean up any existing artefacts in the dist folder.

        Ensures that the dist folder exists, and *doesn't* contain the distribution
        artefact.

        :param app: The app being packaged
        :param options: Any additional arguments passed to the package command. This is
            required because backends that need to *resume* packaging (e.g.,
            notarization on macOS), need to ignore the "clean" behavior and preserve the
            existing artefact.
        """
        if self.distribution_path(app).exists():
            self.distribution_path(app).unlink()
        else:
            # Ensure the dist folder exists.
            self.dist_path.mkdir(exist_ok=True)

    def can_resume(self, app, **options):
        """Determine if we can resume a packaging operation.

        The default backend does not support resume; subclasses that support
        resumable operations (e.g., notarization) should override this method.

        :param app: The app being packaged
        :returns: `True` if packaging can be resumed; `False` otherwise.
        """
        return False

    def verify_resume_app(self, app, **options):
        """Verify the app for a resumed packaging operation.

        Called instead of `verify_app` when `can_resume()` returns
        `True`. Verifies that tools are available and the required Python
        version is present, but skips template and app-level checks that
        were validated during the initial packaging pass.

        :param app: app configuration
        """
        self.verify_app_tools(app)
        self.verify_required_python(app)

    def package_app(self, app: FinalizedAppConfig, **options):
        """Package an application.

        :param app: The application to package
        """
        # Default implementation; nothing to do.

    def _package_app(
        self,
        app: FinalizedAppConfig,
        update: bool,
        packaging_format: str,
        **options,
    ) -> dict | None:
        """Internal method to invoke packaging on a single app. Ensures the app exists,
        and has been updated (if requested) before attempting to issue the actual
        package command.

        :param app: The application to package
        :param update: Should the application be updated (and rebuilt) first?
        :param packaging_format: The format of the packaging artefact to create.
        """
        # Annotate the packaging format onto the app so that distribution path
        # resolution works correctly during the resume check.
        app.packaging_format = packaging_format

        resume = self.can_resume(app, **options)

        if resume:
            state = None
        elif app.external_package_path:
            if not self.supports_external_packaging:
                raise BriefcaseCommandError(
                    f"Briefcase cannot package external {self.platform} apps "
                    f"in {self.output_format} format."
                )

            self.console.info(
                f"Packaging external content from {self.package_path(app)}",
                prefix=app.app_name,
            )

            # A minimal template is required to provide packaging configuration files
            # and other metadata. We *always* generate the template to ensure that
            # packaging metadata is up-to-date. If the app has been packaged before,
            # it will be necessary to confirm deletion of the old folder.
            state = self.create_command(app, **options)
        else:
            template_file = self.bundle_path(app)
            binary_file = self.binary_path(app)

            if not template_file.exists():
                state = self.create_command(app, **options)
                state = self.build_command(app, **full_options(state, options))
            elif update:
                # If we're updating for packaging, update everything.
                # This ensures everything in the packaged artefact is up to date,
                # and is in a production state
                state = self.update_command(
                    app,
                    update_resources=True,
                    update_requirements=True,
                    update_support=True,
                    **options,
                )
                state = self.build_command(app, **full_options(state, options))
            elif not binary_file.exists():
                state = self.build_command(app, **options)
            else:
                state = None

        if resume:
            self.verify_resume_app(app, **options)
        else:
            self.verify_app(app)
            self.clean_dist_folder(app, **options)

        # Package the app
        state = self.package_app(app, **full_options(state, options))

        filename = self.distribution_path(app).relative_to(self.base_path)
        self.console.info(f"Packaged {filename}", prefix=app.app_name)
        return state

    def add_options(self, parser):
        parser.add_argument(
            "-a",
            "--app",
            dest="app_name",
            help="Name of the app to package (if multiple apps exist in the project)",
            default=argparse.SUPPRESS,
        )

        parser.add_argument(
            "-u",
            "--update",
            action="store_true",
            help="Update the app before packaging",
        )
        parser.add_argument(
            "-p",
            "--packaging-format",
            dest="packaging_format",
            help="Packaging format to use",
            default=self.default_packaging_format,
            choices=self.packaging_formats,
        )

        # --adhoc-sign and --identity are mutually exclusive
        signing_group = parser.add_mutually_exclusive_group()
        signing_group.add_argument(
            "--adhoc-sign",
            help=self.ADHOC_SIGN_HELP,
            action="store_true",
        )
        signing_group.add_argument(
            "-i",
            "--identity",
            dest="identity",
            help=self.IDENTITY_HELP,
            required=False,
        )

    def __call__(
        self,
        app: AppConfig | None = None,
        app_name: str | None = None,
        update: bool = False,
        **options,
    ) -> dict | None:
        apps_to_package = self.resolve_apps(app=app, app_name=app_name)

        # Confirm host compatibility, that all required tools are available,
        # and that the app configuration is finalized.
        finalized_apps = self.finalize(apps=apps_to_package.values())

        state = None
        for _, app_obj in sorted(finalized_apps.items()):
            state = self._package_app(
                app_obj,
                update=update,
                **full_options(state, options),
            )

        return state
