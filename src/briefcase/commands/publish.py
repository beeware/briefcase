from briefcase.config import BaseConfig
from briefcase.exceptions import BriefcaseCommandError

from .base import BaseCommand, full_options


class PublishCommand(BaseCommand):
    command = "publish"
    description = "Publish an app to a distribution channel."

    @property
    def publication_channels(self):
        """The list of publication channel backends that are available for this
        format."""
        return ["s3"]

    @property
    def default_publication_channel(self):
        """The default publication channel for this format."""
        return "s3"

    def add_options(self, parser):
        parser.add_argument(
            "-c",
            "--channel",
            choices=self.publication_channels,
            default=self.default_publication_channel,
            help="The channel to publish to",
        )

    def publish_app(self, app: BaseConfig, channel: str, **options):
        """Publish an application.

        :param app: The application to publish
        :param channel: The publication channel to use
        """
        self.logger.info(
            f"TODO: Publish {app.app_name} to {channel}"
        )  # pragma: no cover

    def _publish_app(self, app: BaseConfig, channel: str, **options):
        """Internal method to publish a single app. Ensures the app exists, and has been
        packaged before attempting to issue the actual publish command.

        :param app: The application to publish
        :param channel: The publication channel to use
        """
        # TODO: Verify the app has been packaged
        state = None
        self.verify_app_tools(app)

        state = self.publish_app(app, channel=channel, **full_options(state, options))

        return state

    def __call__(self, channel=None, **options):
        # Confirm host compatibility, that all required tools are available,
        # and that all app configurations are finalized.
        self.finalize()

        # Check the apps have been built first.
        for app_name, app in self.apps.items():
            binary_file = self.binary_path(app)
            if not binary_file.exists():
                raise BriefcaseCommandError(
                    f"Application {app_name} has not been built. "
                    "Build (and test!) the app before publishing."
                )

        # Then publish them all to the selected channel.
        state = None
        for app_name, app in sorted(self.apps.items()):
            state = self._publish_app(
                app, channel=channel, **full_options(state, options)
            )

        return state
