import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    OpenCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import BaseConfig


class StaticWebMixin:
    output_format = "static"
    platform = "web"

    @property
    def packaging_formats(self):
        return ["zip"]

    @property
    def default_packaging_format(self):
        return "zip"

    def project_path(self, app):
        return self.bundle_path(app) / "www"

    def binary_path(self, app):
        return self.bundle_path(app) / "www" / "index.html"

    def distribution_path(self, app, packaging_format):
        return self.binary_path(app)


class StaticWebCreateCommand(StaticWebMixin, CreateCommand):
    description = "Create and populate a static web project."


class StaticWebUpdateCommand(StaticWebCreateCommand, UpdateCommand):
    description = "Update an existing static web project."


class StaticWebOpenCommand(StaticWebMixin, OpenCommand):
    description = "Open an existing static web project."


class StaticWebBuildCommand(StaticWebMixin, BuildCommand):
    description = "Build a static web project."

    def build_app(self, app: BaseConfig, **kwargs):
        """Build the static web deployment for the application.

        :param app: The application to build
        """
        self.logger.info("Building web project...", prefix=app.app_name)
        with self.input.wait_bar("Building..."):
            pass

        return {}


class HTTPHandler(SimpleHTTPRequestHandler):
    """Convert any HTTP request into a path request on the static content
    folder."""

    def translate_path(self, path):
        return str(self.server.base_path / path[1:])


class LocalHTTPServer(HTTPServer):
    """A HTTP server that serves local static content."""

    def __init__(self, base_path, host, port, RequestHandlerClass=HTTPHandler):
        self.base_path = base_path
        super().__init__((host, port), RequestHandlerClass)


class StaticWebRunCommand(StaticWebMixin, RunCommand):
    description = "Run a static web project."

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "--host",
            default="localhost",
            help="The host on which to run the server (default: localhost)",
            required=False,
        )
        parser.add_argument(
            "-p",
            "--port",
            default=8080,
            type=int,
            help="The port on which to run the server (default: 8080)",
            required=False,
        )
        parser.add_argument(
            "--no-browser",
            action="store_false",
            dest="open_browser",
            help="Don't open a web browser on the newly opened server.",
            required=False,
        )

    def run_app(self, app: BaseConfig, host, port, open_browser, **kwargs):
        """Start the application.

        :param app: The config object for the app
        :param host: The host on which to run the server
        :param port: The device UDID to target. If ``None``, the user will
            be asked to select a device at runtime.
        :param open_browser: Should a browser be opened on the newly
        """
        self.logger.info(
            f"Starting web server on http://{host}:{port}/",
            prefix=app.app_name,
        )

        try:
            # Create a local HTTP server
            httpd = LocalHTTPServer(
                self.project_path(app),
                host=host,
                port=port,
            )

            # If requested, open a brower tab on the newly opened server.
            if open_browser:
                webbrowser.open_new_tab(f"http://{host}:{port}")

            self.logger.info(
                "Web server log output (type CTRL-C to stop log)...",
                prefix=app.app_name,
            )
            self.logger.info("=" * 75)

            # Run the server.
            httpd.serve_forever()
        except KeyboardInterrupt:
            # CTRL-C is the accepted way to stop the server.
            pass
        finally:
            with self.input.wait_bar("Shutting down server..."):
                httpd.server_close()

        return {}


class StaticWebPackageCommand(StaticWebMixin, PackageCommand):
    description = "Package an iOS app."


class StaticWebPublishCommand(StaticWebMixin, PublishCommand):
    description = "Publish an iOS app."
    publication_channels = ["s3"]
    default_publication_channel = "s3"


# Declare the briefcase command bindings
create = StaticWebCreateCommand  # noqa
update = StaticWebUpdateCommand  # noqa
open = StaticWebOpenCommand  # noqa
build = StaticWebBuildCommand  # noqa
run = StaticWebRunCommand  # noqa
package = StaticWebPackageCommand  # noqa
publish = StaticWebPublishCommand  # noqa
