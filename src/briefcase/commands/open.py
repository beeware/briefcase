from __future__ import annotations

from abc import abstractmethod

from briefcase.config import AppConfig

from .base import BaseCommand, full_options


class OpenCommand(BaseCommand):
    command = "open"
    description = "Open an app in the build tool for the target platform."

    @abstractmethod
    def project_path(self, app: AppConfig):
        """The path in to the project to pass to the shell to open the project."""

    def _open_app(self, app: AppConfig):
        if self.tools.host_os == "Windows":  # pragma: no-cover-if-not-windows
            self.tools.os.startfile(self.project_path(app))
        elif self.tools.host_os == "Darwin":  # pragma: no-cover-if-not-macos
            self.tools.subprocess.Popen(["open", self.project_path(app)])
        else:  # pragma: no-cover-if-not-linux
            self.tools.subprocess.Popen(["xdg-open", self.project_path(app)])

    def open_app(self, app: AppConfig, **options):
        """Open the project for an app.

        :param app: The application to open
        """
        project_path = self.project_path(app)
        if not project_path.exists():
            state = self.create_command(app, **options)
        else:
            state = None

        self.verify_app(app)

        self.logger.info(
            f"Opening {self.project_path(app).relative_to(self.base_path)}...",
            prefix=app.app_name,
        )
        self._open_app(app)

        return state

    def __call__(self, app: AppConfig | None = None, **options):
        # Confirm host compatibility, that all required tools are available,
        # and that the app configuration is finalized.
        self.finalize(app)

        if app:
            state = self.open_app(app, **options)
        else:
            state = None
            for app_name, app in sorted(self.apps.items()):
                state = self.open_app(app, **full_options(state, options))

        return state
