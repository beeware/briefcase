from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from briefcase.config import AppConfig
    from briefcase.console import Console
    from briefcase.integrations.base import ToolCache


@runtime_checkable
class PackageCommandAPI(Protocol):
    """Stable API surface exposed to packaging format plugins.

    This defines the minimal set of attributes and methods that a plugin
    can rely on from the ``command`` parameter passed to ``package_app()``.
    """

    console: Console
    tools: ToolCache
    dist_path: Path
    base_path: Path

    def distribution_path(self, app: AppConfig) -> Path: ...

    def package_path(self, app: AppConfig) -> Path: ...

    def archive_app(self, app: AppConfig, path: Path): ...


@runtime_checkable
class WindowsPackageCommandAPI(PackageCommandAPI, Protocol):
    """Extension of PackageCommandAPI for Windows-specific features."""

    def sign_app(self, app: AppConfig, identity: str): ...

    def sign_file(
        self,
        app: AppConfig,
        filepath: Path,
        identity: str,
        file_digest: str,
        use_local_machine: bool,
        cert_store: str,
        timestamp_url: str,
        timestamp_digest: str,
    ): ...


@runtime_checkable
class macOSPackageCommandAPI(PackageCommandAPI, Protocol):
    """Extension of PackageCommandAPI for macOS-specific features."""

    dmgbuild: any  # The dmgbuild module if available

    def sign_app(self, app: AppConfig, identity: str): ...

    def sign_file(self, path: Path, identity: str): ...

    def select_identity(self, identity=None, app_identity=None, allow_adhoc=True): ...

    def notarize(self, app: AppConfig, identity: str): ...

    def archive_app(self, app: AppConfig, path: Path): ...

    def ditto_archive(self, source: Path, destination: Path): ...

    def validate_submission_id(self, app, identity, submission_id): ...

    def finalize_notarization(self, app, identity, submission_id): ...


class BasePackagingFormat(ABC):
    """Definition for a plugin that defines a new Briefcase packaging format."""

    def __init__(self, command: PackageCommandAPI):
        self.command = command

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the packaging format."""

    @abstractmethod
    def package_app(self, app: AppConfig, **options):
        """Package the application for this format.

        :param app: The application to package
        :param options: The options for the command
        """

    @abstractmethod
    def distribution_path(self, app: AppConfig) -> Path:
        """The path to the distributable artefact for the app.

        :param app: The app config
        """

    @abstractmethod
    def priority(self, app: AppConfig) -> int:
        """The priority of the packaging format.

        A priority of 0 means the format is not usable. Values 1-10 indicate relative
        preference.
        """
