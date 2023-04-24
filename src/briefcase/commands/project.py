from typing import Optional

from briefcase.commands.base import BaseCommand
from briefcase.config import BaseConfig


class ProjectCommand(BaseCommand):
    command = "project"
    description = "project test."
    output_format = None
    platform = "all"

    def add_options(self, parser):
        parser.add_argument(
            "action",
            help="The app to run",
        )

    def binary_path(self, app):
        NotImplementedError()

    def __call__(
        self,
        app: Optional[BaseConfig] = None,
        update_requirements: bool = False,
        update_resources: bool = False,
        test_mode: bool = False,
        **options,
    ):
        app = list(self.apps.values())[0]
        self.finalize(app)
        self.logger.print(f"project.version={app.version}")
        return app.version
