from unittest import mock

import pytest

from briefcase.channels.base import BasePublicationChannel
from briefcase.commands.base import full_options
from briefcase.platforms.linux.system import LinuxSystemPublishCommand


class DummyLinuxSystemPublishCommand(LinuxSystemPublishCommand):
    """A publish command that tracks the package command invocations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.actions = []

    def package_command(self, app, **kwargs):
        self.actions.append(("package", app.app_name, kwargs.copy()))
        # Remove arguments consumed by the underlying call to package_app()
        kwargs.pop("update", None)
        kwargs.pop("packaging_format", None)
        return full_options({"package_state": app.app_name}, kwargs)


@pytest.fixture
def publish_command(mock_tools, dummy_console, first_app, tmp_path):
    command = DummyLinuxSystemPublishCommand(
        console=dummy_console,
        tools=mock_tools,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    mock_tools.host_os = "Linux"

    # Run outside docker for these tests.
    command.target_image = None

    return command


@pytest.mark.parametrize(
    ("packaging_format", "expected"),
    [
        # The "system" alias uses the finalized packaging format
        ("system", "rpm"),
        # An explicit format is passed through and annotated onto the app
        ("deb", "deb"),
    ],
)
def test_publish_app_packaging_format(
    publish_command,
    first_app,
    packaging_format,
    expected,
    tmp_path,
):
    """The packaging format requested on the command line is resolved before use."""
    # The app has been finalized with a concrete packaging format.
    first_app.packaging_format = "rpm"

    channel = mock.MagicMock(spec_set=BasePublicationChannel)
    channel.publish_app.return_value = {"publish_state": "first-app"}

    # The distribution artefact doesn't exist, so packaging will be triggered.
    publish_command.distribution_path = mock.MagicMock(
        return_value=tmp_path / "base_path" / "dist" / f"first-app.{expected}"
    )
    publish_command.verify_app = mock.MagicMock()

    state = publish_command._publish_app(
        first_app,
        update=False,
        packaging_format=packaging_format,
        channel=channel,
    )

    # The concrete packaging format was annotated onto the app, and used when
    # triggering the package command.
    assert first_app.packaging_format == expected
    assert publish_command.actions == [
        ("package", "first-app", {"update": False, "packaging_format": expected})
    ]

    # The app was published to the requested channel.
    channel.publish_app.assert_called_once_with(
        first_app,
        command=publish_command,
        package_state="first-app",
    )

    assert state == {"publish_state": "first-app"}
