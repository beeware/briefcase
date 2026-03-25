import pytest

from briefcase.channels import (
    get_publication_channel,
    get_publication_channels,
)
from briefcase.channels.appstore import AppStorePublicationChannel
from briefcase.channels.base import (
    BasePublicationChannel,
    PublishCommandAPI,
)
from briefcase.channels.playstore import PlayStorePublicationChannel
from briefcase.exceptions import BriefcaseCommandError


def test_publish_command_api_is_runtime_checkable():
    """An object with the required attributes satisfies PublishCommandAPI."""

    class Conforming:
        console = None
        tools = None
        dist_path = None

        def distribution_path(self, app):
            pass

    assert isinstance(Conforming(), PublishCommandAPI)


def test_publish_command_api_rejects_incomplete():
    """An object missing required attributes does not satisfy PublishCommandAPI."""

    class Missing:
        console = None

    assert not isinstance(Missing(), PublishCommandAPI)


def test_get_publication_channels_no_match():
    """An unregistered platform/format combination returns an empty dict."""
    assert get_publication_channels("tester", "dummy") == {}


def test_appstore_channel():
    """App Store placeholder channel has the expected interface."""
    channel = AppStorePublicationChannel()
    assert isinstance(channel, BasePublicationChannel)
    assert channel.name == "appstore"


def test_playstore_channel():
    """Play Store placeholder channel has the expected interface."""
    channel = PlayStorePublicationChannel()
    assert isinstance(channel, BasePublicationChannel)
    assert channel.name == "playstore"


@pytest.mark.parametrize(
    ("channel_class", "match"),
    [
        (AppStorePublicationChannel, "iOS App Store is not yet implemented"),
        (PlayStorePublicationChannel, "Google Play Store is not yet implemented"),
    ],
)
def test_placeholder_channel_raises(channel_class, match):
    """Placeholder channels raise an error when publish_app is called."""
    channel = channel_class()
    with pytest.raises(BriefcaseCommandError, match=match):
        channel.publish_app(app=None, command=None)


@pytest.mark.parametrize(
    ("platform", "output_format", "channel", "channel_class"),
    [
        ("iOS", "Xcode", "appstore", AppStorePublicationChannel),
        ("android", "gradle", "playstore", PlayStorePublicationChannel),
    ],
)
def test_get_publication_channels_discovery(
    platform,
    output_format,
    channel,
    channel_class,
):
    """Built-in channels are discovered via entry points."""
    channels = get_publication_channels(platform, output_format)
    assert channels[channel] is channel_class


def test_get_publication_channel():
    """A channel can be retrieved by name."""
    assert isinstance(
        get_publication_channel("appstore", "iOS", "Xcode"),
        AppStorePublicationChannel,
    )


@pytest.mark.parametrize(
    ("platform", "output_format", "channel"),
    [
        # Completely unknown
        ("flat", "wrapped", "something"),
        # Known platform, but unknown format
        ("iOS", "Xcode", "something"),
        # Known format on a different platform
        ("iOS", "Xcode", "playstore"),
    ],
)
def test_get_publication_channel_unknown(platform, output_format, channel):
    """Requesting an unknown channel raises an error."""
    with pytest.raises(
        BriefcaseCommandError,
        match=f"Unknown publication channel: {channel}",
    ):
        get_publication_channel(channel, platform, output_format)
