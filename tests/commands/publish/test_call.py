import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_publish(publish_command, first_app, second_app):
    """If there are multiple apps, publish all of them."""
    # Add two apps
    publish_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options, _ = publish_command.parse_options([])

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


def test_non_existent(publish_command, first_app_config, second_app):
    """Requesting a publish of a non-existent app raises an error."""
    # Add two apps; use the "config only" version of the first app.
    publish_command.apps = {
        "first": first_app_config,
        "second": second_app,
    }

    # Configure no command line options
    options, _ = publish_command.parse_options([])

    # Invoking the publish command raises an error
    with pytest.raises(BriefcaseCommandError):
        publish_command(**options)

    # Only verification will be performed
    assert publish_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
    ]


def test_unbuilt(publish_command, first_app_unbuilt, second_app):
    """Requesting a publish of an app that has been created, but not built, raises an
    error."""
    # Add two apps; use the "config only" version of the first app.
    publish_command.apps = {
        "first": first_app_unbuilt,
        "second": second_app,
    }

    # Configure no command line options
    options, _ = publish_command.parse_options([])

    # Invoking the publish command raises an error
    with pytest.raises(BriefcaseCommandError):
        publish_command(**options)

    # Only verification will be performed
    assert publish_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
    ]
