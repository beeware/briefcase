from __future__ import annotations

from typing import TYPE_CHECKING

from briefcase.channels.base import BasePublicationChannel
from briefcase.exceptions import BriefcaseCommandError

if TYPE_CHECKING:
    from briefcase.channels.base import PublishCommandAPI
    from briefcase.config import AppConfig


class AppStorePublicationChannel(BasePublicationChannel):
    """Placeholder for iOS App Store publication channel."""

    @property
    def name(self) -> str:
        return "appstore"

    def publish_app(self, app: AppConfig, command: PublishCommandAPI, **options):
        raise BriefcaseCommandError(
            "Publishing to the iOS App Store is not yet implemented.\n"
            "\n"
            "See https://github.com/beeware/briefcase/issues/2697 for progress."
        )
