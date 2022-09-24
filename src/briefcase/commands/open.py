from typing import Optional

from briefcase.config import BaseConfig

from .base import BaseCommand, full_options


class OpenCommand(BaseCommand):
    command = "open"

    def open_project(self, project_path):
        if self.tools.host_os == "Windows":
            self.tools.os.startfile(project_path)
        elif self.tools.host_os == "Darwin":
            self.tools.subprocess.Popen(["open", project_path])
        else:
            self.tools.subprocess.Popen(["xdg-open", project_path])

    def open_app(self, app: BaseConfig, **options):
        """Open the project for an app.

        :param app: The application to open
        """
        project_path = self.project_path(app)
        if not project_path.exists():
            state = self.create_command(app, **options)
        else:
            state = None

        self.verify_app_tools(app)

        self.logger.info(
            f"Opening {self.project_path(app).relative_to(self.base_path)}...",
            prefix=app.app_name,
        )
        self.open_project(project_path)

        return state

    def __call__(self, app: Optional[BaseConfig] = None, **options):
        # Confirm all required tools are available
        self.verify_tools()

        if app:
            state = self.open_app(app, **options)
        else:
            state = None
            for app_name, app in sorted(self.apps.items()):
                state = self.open_app(app, **full_options(state, options))

        return state
