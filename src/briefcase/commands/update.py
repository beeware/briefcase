from pathlib import Path
from typing import Optional

from briefcase.config import BaseConfig

from .create import CreateCommand


class UpdateCommand(CreateCommand):
    def update_app(self, app: BaseConfig, base_path: Path):
        """
        Update an existing application bundle.

        :param app: The config object for the app
        :param base_path: The path to the project directory.
        """
        bundle_path = self.bundle_path(app, base_path)
        if not bundle_path.exists():
            print("{app.name} does not exist; call create first!".format(
                app=app
            ))
            return

        print()
        print('[{app.name}] Update dependencies...'.format(
            app=app
        ))
        self.install_app_dependencies(app=app, base_path=base_path)

        print()
        print('[{app.name}] Update application code...'.format(
            app=app
        ))
        self.install_app_code(app=app, base_path=base_path)

    def __call__(self, app: Optional[BaseConfig] = None, path: Optional[Path] = None):
        if path is None:
            path = Path.cwd()

        self.verify_tools()

        if app:
            self.update_app(app, path)
        else:
            for app_name, app in self.apps.items():
                self.update_app(app, path)
