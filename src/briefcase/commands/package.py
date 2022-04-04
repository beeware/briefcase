from typing import Optional

from briefcase.config import BaseConfig

from .base import BaseCommand, full_options


class PackageCommand(BaseCommand):
    command = 'package'

    @property
    def packaging_formats(self):
        return [self.output_format]

    @property
    def default_packaging_format(self):
        return self.output_format

    def package_app(self, app: BaseConfig, **options):
        """
        Package an application.

        :param app: The application to package
        """
        # Default implementation; nothing to do.

    def _package_app(
        self,
        app: BaseConfig,
        update: bool,
        packaging_format: str,
        **options
    ):
        """
        Internal method to invoke packaging on a single app.
        Ensures the app exists, and has been updated (if requested) before
        attempting to issue the actual package command.

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
            state = self.update_command(app, **options)
            state = self.build_command(app, **full_options(state, options))
        elif not binary_file.exists():
            state = self.build_command(app, **options)
        else:
            state = None

        state = self.package_app(
            app,
            packaging_format=packaging_format,
            **full_options(state, options)
        )

        print()
        print("[{app.app_name}] Packaged {filename}".format(
            app=app,
            filename=self.distribution_path(
                app,
                packaging_format=packaging_format,
            ).relative_to(self.base_path),
        ))
        return state

    def add_options(self, parser):
        parser.add_argument(
            '-p',
            '--packaging-format',
            dest='packaging_format',
            help='Packaging format to use.',
            default=self.default_packaging_format,
            choices=self.packaging_formats,
        )
        parser.add_argument(
            '--no-sign',
            dest='sign_app',
            help='Disable code signing of the app.',
            action='store_false',
        )
        parser.add_argument(
            '--adhoc-sign',
            help='Sign the app with adhoc identity.',
            action='store_true',
        )
        parser.add_argument(
            '-i',
            '--identity',
            dest='identity',
            help='The code signing identity to use; either the 40-digit hex '
                 'checksum, or the full name of the identity.',
            required=False,
        )

    def __call__(
        self,
        app: Optional[BaseConfig] = None,
        update: bool = False,
        **options
    ):
        # Confirm all required tools are available
        self.verify_tools()

        if app:
            state = self._package_app(app, update=update, **options)
        else:
            state = None
            for app_name, app in sorted(self.apps.items()):
                state = self._package_app(
                    app,
                    update=update,
                    **full_options(state, options)
                )

        return state
