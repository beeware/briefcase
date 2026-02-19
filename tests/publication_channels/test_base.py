import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.publication_channels import (
    get_publication_channel,
    get_publication_channels,
)
from briefcase.publication_channels.appstore import AppStorePublicationChannel
from briefcase.publication_channels.base import (
    BasePublicationChannel,
    PublishCommandAPI,
)
from briefcase.publication_channels.playstore import PlayStorePublicationChannel


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


def test_get_publication_channels_discovery():
    """Built-in channels are discovered via entry points."""
    ios_channels = get_publication_channels("ios", "xcode")
    assert ios_channels["appstore"] is AppStorePublicationChannel

    android_channels = get_publication_channels("android", "gradle")
    assert android_channels["playstore"] is PlayStorePublicationChannel


def test_get_publication_channel():
    """A channel can be retrieved by name."""
    assert isinstance(
        get_publication_channel("appstore", "ios", "xcode"),
        AppStorePublicationChannel,
    )


def test_get_publication_channel_unknown():
    """Requesting an unknown channel raises an error."""
    with pytest.raises(
        BriefcaseCommandError,
        match="Unknown publication channel: unknown",
    ):
        get_publication_channel("unknown", "ios", "xcode")
