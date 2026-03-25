from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from briefcase.config import AppConfig
    from briefcase.console import Console
    from briefcase.integrations.base import ToolCache


@runtime_checkable
class PublishCommandAPI(Protocol):
    """Stable API surface exposed to publication channel plugins.

    This defines the minimal set of attributes and methods that a plugin
    can rely on from the ``command`` parameter passed to ``publish_app()``.
    """

    console: Console
    tools: ToolCache
    dist_path: Path

    def distribution_path(self, app: AppConfig) -> Path: ...


class BasePublicationChannel(ABC):
    """Definition for a plugin that defines a new Briefcase publication channel."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the publication channel."""

    @abstractmethod
    def publish_app(self, app: AppConfig, command: PublishCommandAPI, **options):
        """Publish an application to this channel.

        :param app: The application to publish
        :param command: The publish command instance
        """
