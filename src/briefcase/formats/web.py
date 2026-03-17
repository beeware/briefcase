from __future__ import annotations

from pathlib import Path

from briefcase.config import AppConfig
from briefcase.formats.zip import ZipPackagingFormat


class WebZipPackagingFormat(ZipPackagingFormat):
    def distribution_path(self, app: AppConfig) -> Path:
        return self.command.dist_path / f"{app.formal_name}-{app.version}.web.zip"

    def package_app(self, app: AppConfig, **kwargs):
        self.command.console.info(
            "Packaging web app for distribution...",
            prefix=app.app_name,
        )

        with self.command.console.wait_bar("Building archive..."):
            self.command.archive_app(app, self.distribution_path(app))

    def priority(self, app: AppConfig) -> int:
        return 10
