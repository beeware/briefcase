from typing import Optional

from briefcase.config import BaseConfig

from .create import CreateCommand


class UpdateCommand(CreateCommand):
    def add_options(self, parser):
        parser.add_argument(
            '-d',
            '--update_dependencies',
            action="store_true",
            help='Update dependencies for app'
        )
        parser.add_argument(
            '-e',
            '--update_extra',
            action="store_true",
            help='Update extra app resources'
        )

    def update_app(self, app: BaseConfig, update_dependencies=False, update_extras=False):
        """
        Update an existing application bundle.

        :param app: The config object for the app
        :param update_dependencies: Should dependencies be updated? (default: False)
        :param update_extras: Should extra resources be updated? (default: False)
        """
        bundle_path = self.bundle_path(app)
        if not bundle_path.exists():
            print()
            print("[{app.name}] Application does not exist; call create first!".format(
                app=app
            ))
            return

        if update_dependencies:
            print()
            print('[{app.name}] Updating dependencies...'.format(
                app=app
            ))
            self.install_app_dependencies(app=app)

        print()
        print('[{app.name}] Updating application code...'.format(
            app=app
        ))
        self.install_app_code(app=app)

        if update_extras:
            print()
            print('[{app.name}] Updating extra application resources...'.format(
                app=app
            ))
            self.install_app_extras(app=app)

        print()
        print('[{app.name}] Application updated.'.format(
            app=app
        ))

    def __call__(self, app: Optional[BaseConfig] = None):
        self.verify_tools()

        if app:
            self.update_app(
                app,
                update_dependencies=self.options.update_dependencies,
                update_extras=self.options.update_extra,
            )
        else:
            for app_name, app in sorted(self.apps.items()):
                self.update_app(
                    app,
                    update_dependencies=self.options.update_dependencies,
                    update_extras=self.options.update_extra,
                )
