from __future__ import annotations

import argparse

from briefcase.channels import get_publication_channels
from briefcase.channels.base import BasePublicationChannel
from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError

from .base import BaseCommand, full_options


class PublishCommand(BaseCommand):
    command = "publish"
    description = "Publish an app to a distribution channel."

    @property
    def packaging_formats(self):
        return [self.output_format]

    @property
    def default_packaging_format(self):
        return self.output_format

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
            "-u",
            "--update",
            action="store_true",
            help="Update the app before publishing",
        )
        parser.add_argument(
            "-p",
            "--packaging-format",
            dest="packaging_format",
            help="Packaging format to publish",
            default=self.default_packaging_format,
            choices=self.packaging_formats,
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
        update: bool,
        packaging_format: str,
        channel: BasePublicationChannel,
        **options,
    ) -> dict | None:
        """Internal method to publish a single app.

        :param app: The application to publish
        :param update: Should the application be updated (and rebuilt) first?
        :param packaging_format: The format of the packaging artefact to create.
        :param channel: The resolved BasePublicationChannel instance
        """
        state = None

        # Annotate the packaging format onto the app
        app.packaging_format = packaging_format

        if update or not self.distribution_path(app).exists():
            state = self.package_command(
                app,
                update=update,
                packaging_format=packaging_format,
                **options,
            )

        self.verify_app(app)

        state = channel.publish_app(app, command=self, **full_options(state, options))

        return state

    def __call__(
        self,
        app: AppConfig | None = None,
        app_name: str | None = None,
        update: bool | None = False,
        packaging_format: str | None = None,
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

        # Publish all apps to the selected channel.
        state = None
        for _, app_obj in sorted(apps_to_publish.items()):
            state = self._publish_app(
                app_obj,
                update=update,
                packaging_format=packaging_format or self.default_packaging_format,
                channel=resolved_channel,
                **full_options(state, options),
            )

        return state
