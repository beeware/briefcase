from __future__ import annotations

import argparse

from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError
from briefcase.publication_channels import get_publication_channels
from briefcase.publication_channels.base import BasePublicationChannel

from .base import BaseCommand, full_options


class PublishCommand(BaseCommand):
    command = "publish"
    description = "Publish an app to a distribution channel."

    def _get_channels(self) -> dict[str, type[BasePublicationChannel]]:
        """Discover available publication channels for this platform/format."""
        return get_publication_channels(self.platform, self.output_format)

    def add_options(self, parser: argparse.ArgumentParser) -> None:
        channels = self._get_channels()
        channel_names = sorted(channels.keys())

        parser.add_argument(
            "-a",
            "--app",
            dest="app_name",
            help="Name of the app to publish (if multiple apps exist in the project)",
            default=argparse.SUPPRESS,
        )
        parser.add_argument(
            "-c",
            "--channel",
            choices=channel_names or None,
            default=None,
            help="The channel to publish to",
        )

    def _publish_app(
        self,
        app: AppConfig,
        channel: BasePublicationChannel,
        **options,
    ) -> dict | None:
        """Internal method to publish a single app.

        :param app: The application to publish
        :param channel: The resolved BasePublicationChannel instance
        """
        state = None

        if not self.distribution_path(app).exists():
            state = self.package_command(app, **options)

        self.verify_app(app)

        state = channel.publish_app(app, command=self, **full_options(state, options))

        return state

    def __call__(
        self,
        app: AppConfig | None = None,
        app_name: str | None = None,
        channel: str | None = None,
        **options,
    ) -> dict | None:
        apps_to_publish = self.resolve_apps(app=app, app_name=app_name)

        # Verify that at least one publication channel is available.
        channels = self._get_channels()
        if not channels:
            raise BriefcaseCommandError(
                f"No publication channels are available for "
                f"{self.platform} {self.output_format}.\n\n"
                f"Install a publication channel plugin and try again."
            )

        if channel is None:
            if len(channels) == 1:
                resolved_channel = next(iter(channels.values()))()
            else:
                raise BriefcaseCommandError(
                    f"Multiple publication channels are available for "
                    f"{self.platform} {self.output_format}: "
                    f"{', '.join(sorted(channels))}.\n\n"
                    f"Specify a channel with --channel."
                )
        else:
            resolved_channel = channels[channel]()

        # Confirm host compatibility, that all required tools are available,
        # and that all app configurations are finalized.
        self.finalize(apps=apps_to_publish.values())

        # Check the apps have been built first.
        for app_name_key, app_obj in apps_to_publish.items():
            binary_file = self.binary_path(app_obj)
            if not binary_file.exists():
                raise BriefcaseCommandError(
                    f"Application {app_name_key} has not been built. "
                    "Build (and test!) the app before publishing."
                )

        # Then publish them all to the selected channel.
        state = None
        for _, app_obj in sorted(apps_to_publish.items()):
            state = self._publish_app(
                app_obj, channel=resolved_channel, **full_options(state, options)
            )

        return state
