from __future__ import annotations

from importlib.metadata import entry_points

from briefcase.exceptions import BriefcaseCommandError
from briefcase.publication_channels.base import (
    BasePublicationChannel,
    PublishCommandAPI,  # noqa: F401
)


def get_publication_channels(
    platform: str,
    output_format: str,
) -> dict[str, type[BasePublicationChannel]]:
    """Load built-in and third-party publication channels for a platform/format.

    :param platform: The target platform (e.g., "ios")
    :param output_format: The output format (e.g., "xcode")
    :returns: A dict mapping channel names to channel classes.
    """
    return {
        ep.name: ep.load()
        for ep in entry_points(
            group=f"briefcase.publication_channels.{platform}.{output_format}"
        )
    }


def get_publication_channel(
    name: str,
    platform: str,
    output_format: str,
) -> BasePublicationChannel:
    """Get a publication channel by name for a platform/format.

    :param name: The channel name
    :param platform: The target platform
    :param output_format: The output format
    :returns: An instantiated publication channel.
    """
    channels = get_publication_channels(platform, output_format)
    if name not in channels:
        available = ", ".join(sorted(channels)) or "none"
        raise BriefcaseCommandError(
            f"Unknown publication channel: {name}\n\n"
            f"Available channels for {platform}/{output_format}: {available}"
        )
    return channels[name]()
