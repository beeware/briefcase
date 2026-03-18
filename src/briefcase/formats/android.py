from __future__ import annotations

import subprocess
from pathlib import Path

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.formats.base import BasePackagingFormat


class AndroidPackagingFormat(BasePackagingFormat):
    def priority(self, app: AppConfig) -> int:
        return 0

    def distribution_path(self, app: AppConfig) -> Path:
        # This will be overridden by subclasses or needs to be consistent
        # with what GradlePackageCommand expects.
        return self.command.dist_path / self.distribution_filename(app)

    def distribution_filename(self, app: AppConfig) -> str:
        raise NotImplementedError()

    def _build_android(self, app: AppConfig, build_type: str, build_artefact_path: str):
        with self.command.console.wait_bar("Bundling..."):
            try:
                self.command.run_gradle(app, [build_type])
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError("Error while building project.") from e

        # Move artefact to final location.
        self.command.tools.shutil.move(
            self.command.bundle_path(app) / "app/build/outputs" / build_artefact_path,
            self.distribution_path(app),
        )


class AndroidAABPackagingFormat(AndroidPackagingFormat):
    @property
    def name(self) -> str:
        return "aab"

    def distribution_filename(self, app: AppConfig) -> str:
        return f"{app.formal_name}-{app.version}.aab"

    def package_app(self, app: AppConfig, **kwargs):
        self.command.console.info(
            "Building Android App Bundle in release mode...",
            prefix=app.app_name,
        )
        self._build_android(app, "bundleRelease", "bundle/release/app-release.aab")

    def priority(self, app: AppConfig) -> int:
        return 10


class AndroidAPKPackagingFormat(AndroidPackagingFormat):
    @property
    def name(self) -> str:
        return "apk"

    def distribution_filename(self, app: AppConfig) -> str:
        return f"{app.formal_name}-{app.version}.apk"

    def package_app(self, app: AppConfig, **kwargs):
        self.command.console.info(
            "Building Android APK in release mode...",
            prefix=app.app_name,
        )
        self._build_android(
            app, "assembleRelease", "apk/release/app-release-unsigned.apk"
        )

    def priority(self, app: AppConfig) -> int:
        return 1


class AndroidDebugAPKPackagingFormat(AndroidPackagingFormat):
    @property
    def name(self) -> str:
        return "debug-apk"

    def distribution_filename(self, app: AppConfig) -> str:
        return f"{app.formal_name}-{app.version}.debug.apk"

    def package_app(self, app: AppConfig, **kwargs):
        self.command.console.info(
            "Building Android App in debug mode...",
            prefix=app.app_name,
        )
        self._build_android(app, "assembleDebug", "apk/debug/app-debug.apk")
