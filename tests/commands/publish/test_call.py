import pytest

from briefcase.exceptions import BriefcaseCommandError

from .conftest import _make_channel_class


def test_channel_classes_are_instantiated(publish_command, first_app):
    """Channel classes returned by _get_channels are instantiated before use."""
    instantiated = []

    SpyChannel = _make_channel_class("spy")
    original_init = SpyChannel.__init__

    def tracking_init(self):
        instantiated.append(True)
        original_init(self)

    SpyChannel.__init__ = tracking_init

    # _get_channels returns classes, matching the real entry_points().load() behavior
    publish_command._get_channels = lambda: {"spy": SpyChannel}
    publish_command.apps = {"first": first_app}

    publish_command(channel="spy")

    assert len(instantiated) == 1
    assert ("publish", "first", "spy", {}) in publish_command.actions


def test_no_channels(publish_command, first_app):
    """If no publication channels are available, an error is raised."""
    publish_command._get_channels = dict
    publish_command.apps = {"first": first_app}

    options, _ = publish_command.parse_options([])

    with pytest.raises(BriefcaseCommandError, match="No publication channels"):
        publish_command(**options)


def test_multiple_channels_no_flag(publish_command, first_app):
    """Multiple channels without --channel raises an error."""
    publish_command.apps = {"first": first_app}

    with pytest.raises(BriefcaseCommandError, match="Specify a channel"):
        publish_command(channel=None)


def test_single_channel_auto_selects(publish_command, first_app):
    """A single available channel is used automatically."""
    publish_command._get_channels = lambda: {"only": _make_channel_class("only")}
    publish_command.apps = {"first": first_app}

    publish_command(channel=None)

    assert publish_command.actions == [
        ("verify-host",),
        ("verify-tools",),
        ("finalize-app-config", "first"),
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("publish", "first", "only", {}),
    ]


def test_publish_triggers_package(publish_command, first_app_unpackaged):
    """If distribution artefact is missing, package is triggered first."""
    publish_command._get_channels = lambda: {"only": _make_channel_class("only")}
    publish_command.apps = {"first": first_app_unpackaged}
    # binary exists but distribution artefact does not

    publish_command(channel=None)

    assert ("package", "first") in [a[:2] for a in publish_command.actions]


def test_publish_with_update(publish_command, first_app):
    """An app update can be forced before publication."""
    publish_command._get_channels = lambda: {"only": _make_channel_class("only")}
    publish_command.apps = {"first": first_app}

    publish_command(update=True, channel=None)

    assert publish_command.actions == [
        ("verify-host",),
        ("verify-tools",),
        ("finalize-app-config", "first"),
        ("package", "first", {"update": True, "packaging_format": "Dummy"}),
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("publish", "first", "only", {"package_state": "first"}),
    ]


def test_publish(publish_command, first_app, second_app):
    """If there are multiple apps, publish all of them."""
    # Add two apps
    publish_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Select a specific channel (required when multiple are available)
    options, _ = publish_command.parse_options(["-c", "s3"])

    # Run the publish command
    publish_command(**options)

    # The right sequence of things will be done
    assert publish_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # Publish the first app to s3
        ("publish", "first", "s3", {}),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # Publish the second app to s3
        ("publish", "second", "s3", {"publish_state": "first"}),
    ]


def test_publish_alternative_channel(publish_command, first_app, second_app):
    """Apps can be published to an alternate channel."""
    # Add two apps
    publish_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options, _ = publish_command.parse_options(["-c", "alternative"])

    # Run the publish command
    publish_command(**options)

    # The right sequence of things will be done
    assert publish_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # App template is verified for first app
        ("verify-app-template", "first"),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # Publish the first app to the alternative channel
        ("publish", "first", "alternative", {}),
        # App template is verified for second app
        ("verify-app-template", "second"),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # Publish the second app to the alternative channel
        ("publish", "second", "alternative", {"publish_state": "first"}),
    ]


@pytest.mark.parametrize("app_flags", ["--app", "-a"])
def test_publish_app_single(publish_command, first_app, second_app, app_flags):
    """If the --app or -a flag is used, only the selected app is published."""
    # Add two apps
    publish_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options with the parameterized flag
    options, _ = publish_command.parse_options([app_flags, "first", "-c", "s3"])

    # Run the publish command
    publish_command(**options)

    # Only the selected app is published
    assert publish_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # Only the selected app config is finalized
        ("finalize-app-config", "first"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # Publish the selected app
        ("publish", "first", "s3", {}),
    ]


def test_publish_app_invalid(publish_command, first_app, second_app):
    """If an invalid app name is passed to --app, raise an error."""
    # Add two apps
    publish_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure the --app option with an invalid app
    options, _ = publish_command.parse_options(["--app", "invalid", "-c", "s3"])

    # Running the command should raise an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"App 'invalid' does not exist in this project.",
    ):
        publish_command(**options)


def test_publish_passes_packaging_format_to_package(
    publish_command,
    first_app_unpackaged,
):
    """packaging_format is forwarded to package_command when packaging is triggered."""
    publish_command._get_channels = lambda: {"only": _make_channel_class("only")}
    publish_command.apps = {"first": first_app_unpackaged}

    publish_command(channel=None)

    # Find the package action and verify packaging_format was passed
    package_actions = [a for a in publish_command.actions if a[0] == "package"]
    assert len(package_actions) == 1
    assert "packaging_format" in package_actions[0][2]
    assert package_actions[0][2]["packaging_format"] == "Dummy"


def test_non_existent(publish_command, first_app_config, second_app):
    """Publishing an app that hasn't been created cascades through packaging."""
    # Add two apps; use the "config only" version of the first app.
    publish_command.apps = {
        "first": first_app_config,
        "second": second_app,
    }

    options, _ = publish_command.parse_options(["-c", "s3"])

    publish_command(**options)

    assert publish_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # First app: no distribution artefact, so package is triggered
        ("package", "first", {"update": False, "packaging_format": "Dummy"}),
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("publish", "first", "s3", {"package_state": "first"}),
        # Second app publishes normally (has distribution artefact)
        ("verify-app-template", "second"),
        ("verify-app-tools", "second"),
        ("publish", "second", "s3", {"publish_state": "first"}),
    ]


def test_unbuilt(publish_command, first_app_unbuilt, second_app):
    """Publishing an unbuilt app cascades through packaging."""
    publish_command.apps = {
        "first": first_app_unbuilt,
        "second": second_app,
    }

    options, _ = publish_command.parse_options(["-c", "s3"])

    publish_command(**options)

    assert publish_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # First app: no distribution artefact, so package is triggered first
        ("package", "first", {"update": False, "packaging_format": "Dummy"}),
        ("verify-app-template", "first"),
        ("verify-app-tools", "first"),
        ("publish", "first", "s3", {"package_state": "first"}),
        # Second app publishes normally (has distribution artefact)
        ("verify-app-template", "second"),
        ("verify-app-tools", "second"),
        ("publish", "second", "s3", {"publish_state": "first"}),
    ]
