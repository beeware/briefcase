from __future__ import annotations

from pathlib import Path

from briefcase.config import AppConfig
from briefcase.formats.base import BasePackagingFormat


class ZipPackagingFormat(BasePackagingFormat):
    @property
    def name(self) -> str:
        return "zip"

    def distribution_path(self, app: AppConfig) -> Path:
        return self.command.dist_path / f"{app.formal_name}-{app.version}.zip"

    def package_app(self, app: AppConfig, **options):
        """Package the application.

        :param app: The application to package
        :param options: The options for the command
        """
        self.command.archive_app(app, self.distribution_path(app))

    def priority(self, app: AppConfig) -> int:
        # Zip is always available as a fallback, but usually not the default.
        return 1
