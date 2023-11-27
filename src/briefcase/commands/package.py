from __future__ import annotations

from abc import abstractmethod

from briefcase.config import AppConfig

from .base import BaseCommand, full_options


class PackageCommand(BaseCommand):
    command = "package"
    description = "Package an app for distribution."

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

    def package_app(self, app: AppConfig, **options):
        """Package an application.

        :param app: The application to package
        """
        # Default implementation; nothing to do.

    def _package_app(
        self,
        app: AppConfig,
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

        # Annotate the packaging format onto the app
        app.packaging_format = packaging_format

        # Verify the app, which will do final confirmation that we can
        # package in the requested format.
        self.verify_app(app)

        # If the distribution artefact already exists, remove it.
        if self.distribution_path(app).exists():
            self.distribution_path(app).unlink()
        else:
            # Ensure the dist folder exists.
            self.dist_path.mkdir(exist_ok=True)

        # Package the app
        state = self.package_app(app, **full_options(state, options))

        filename = self.distribution_path(app).relative_to(self.base_path)
        self.logger.info(f"Packaged {filename}", prefix=app.app_name)
        return state

    def add_options(self, parser):
        parser.add_argument(
            "-u",
            "--update",
            action="store_true",
            help="Update the app before building",
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
        update: bool = False,
        **options,
    ) -> dict | None:
        # Confirm host compatibility, that all required tools are available,
        # and that the app configuration is finalized.
        self.finalize(app)

        if app:
            state = self._package_app(app, update=update, **options)
        else:
            state = None
            for app_name, app in sorted(self.apps.items()):
                state = self._package_app(
                    app, update=update, **full_options(state, options)
                )

        return state
