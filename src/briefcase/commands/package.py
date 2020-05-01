from typing import Optional

from briefcase.config import BaseConfig

from .base import BaseCommand, full_options


class PackageCommand(BaseCommand):
    command = 'package'

    def package_app(self, app: BaseConfig, **options):
        """
        Package an application.

        :param app: The application to package
        """
        # Default implementation; nothing to do.

    def _package_app(self, app: BaseConfig, update: bool, **options):
        """
        Internal method to invoke packaging on a single app.
        Ensures the app exists, and has been updated (if requested) before
        attempting to issue the actual package command.

        :param app: The application to package
        :param update: Should the application be updated (and rebuilt) first?
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

        state = self.package_app(app, **full_options(state, options))

        print()
        print("[{app.app_name}] Packaged {filename}".format(
            app=app,
            filename=self.distribution_path(app).relative_to(self.base_path),
        ))
        return state

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
                state = self._package_app(app, update=update, **full_options(state, options))

        return state
