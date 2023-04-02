import errno
import subprocess
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import List
from zipfile import ZipFile

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import tomli_w

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    OpenCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import AppConfig
from briefcase.exceptions import BriefcaseCommandError, BriefcaseConfigError


class StaticWebMixin:
    output_format = "static"
    platform = "web"

    def project_path(self, app):
        return self.bundle_path(app) / "www"

    def binary_path(self, app):
        return self.bundle_path(app) / "www" / "index.html"

    def wheel_path(self, app):
        return self.project_path(app) / "static" / "wheels"

    def distribution_path(self, app):
        return self.dist_path / f"{app.formal_name}-{app.version}.web.zip"


class StaticWebCreateCommand(StaticWebMixin, CreateCommand):
    description = "Create and populate a static web project."

    def output_format_template_context(self, app: AppConfig):
        """Add style framework details to the app template."""
        return {
            "style_framework": getattr(app, "style_framework", "None"),
        }


class StaticWebUpdateCommand(StaticWebCreateCommand, UpdateCommand):
    description = "Update an existing static web project."


class StaticWebOpenCommand(StaticWebMixin, OpenCommand):
    description = "Open the folder containing an existing static web project."


class StaticWebBuildCommand(StaticWebMixin, BuildCommand):
    description = "Build a static web project."

    def _trim_file(self, path, sentinel):
        """Re-write a file to strip any content after a sentinel line.

        The file is stored in-memory, so it shouldn't be used on files
        with a *lot* of content before the sentinel.

        :param path: The path to the file to be trimmed
        :param sentinel: The content of the sentinel line. This will
            become the last line in the trimmed file.
        """
        content = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.rstrip("\n") == sentinel:
                    content.append(line)
                    break
                else:
                    content.append(line)

        with path.open("w", encoding="utf-8") as f:
            for line in content:
                f.write(line)

    def _process_wheel(self, wheelfile, css_file):
        """Process a wheel, extracting any content that needs to be compiled into the
        final project.

        :param wheelfile: The path to the wheel file to be processed.
        :param css_file: A file handle, opened for write/append, to which
            any extracted CSS content will be appended.
        """
        package = " ".join(wheelfile.name.split("-")[:2])
        with ZipFile(wheelfile) as wheel:
            for filename in wheel.namelist():
                path = Path(filename)
                # Any CSS file in a `static` folder is appended
                if (
                    len(path.parts) > 1
                    and path.parts[1] == "static"
                    and path.suffix == ".css"
                ):
                    self.logger.info(f"    Found {filename}")
                    css_file.write(
                        "\n/*******************************************************\n"
                    )
                    css_file.write(f" * {package}::{'/'.join(path.parts[2:])}\n")
                    css_file.write(
                        " *******************************************************/\n\n"
                    )
                    css_file.write(wheel.read(filename).decode("utf-8"))

    def build_app(self, app: AppConfig, **kwargs):
        """Build the static web deployment for the application.

        :param app: The application to build
        """
        self.logger.info("Building web project...", prefix=app.app_name)

        if self.wheel_path(app).exists():
            with self.input.wait_bar("Removing old wheels..."):
                self.tools.shutil.rmtree(self.wheel_path(app))

        self.wheel_path(app).mkdir(parents=True)

        with self.input.wait_bar("Building app wheel..."):
            try:
                self.tools.subprocess.run(
                    [
                        sys.executable,
                        "-u",
                        "-m",
                        "wheel",
                        "pack",
                        self.app_path(app),
                        "--dest-dir",
                        self.wheel_path(app),
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to build wheel for app {app.app_name!r}"
                ) from e

        with self.input.wait_bar("Installing wheels for requirements..."):
            try:
                self.tools.subprocess.run(
                    [
                        sys.executable,
                        "-u",
                        "-m",
                        "pip",
                        "wheel",
                        "--wheel-dir",
                        self.wheel_path(app),
                        "-r",
                        self.bundle_path(app) / "requirements.txt",
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to install requirements for app {app.app_name!r}"
                ) from e

        with self.input.wait_bar("Writing Pyscript configuration file..."):
            with (self.project_path(app) / "pyscript.toml").open("wb") as f:
                config = {
                    "name": app.formal_name,
                    "description": app.description,
                    "version": app.version,
                    "splashscreen": {"autoclose": True},
                    "terminal": False,
                    # Ensure that we're using Unix path separators, as the content
                    # will be parsed by pyscript in the browser.
                    "packages": [
                        f'/{"/".join(wheel.relative_to(self.project_path(app)).parts)}'
                        for wheel in sorted(self.wheel_path(app).glob("*.whl"))
                    ],
                }
                # Parse any additional pyscript.toml content, and merge it into
                # the overall content
                try:
                    extra = tomllib.loads(app.extra_pyscript_toml_content)
                    config.update(extra)
                except tomllib.TOMLDecodeError as e:
                    raise BriefcaseConfigError(
                        f"Extra pyscript.toml content isn't valid TOML: {e}"
                    ) from e
                except AttributeError:
                    pass

                # Write the final configuration.
                tomli_w.dump(config, f)

        self.logger.info("Compile static web content from wheels")
        with self.input.wait_bar("Compiling static web content from wheels..."):
            # Trim previously compiled content out of briefcase.css
            briefcase_css_path = (
                self.project_path(app) / "static" / "css" / "briefcase.css"
            )
            self._trim_file(
                briefcase_css_path,
                sentinel=" ******************* Wheel contributed styles **********************/",
            )

            # Extract static resources from packaged wheels
            for wheelfile in sorted(self.wheel_path(app).glob("*.whl")):
                self.logger.info(f"  Processing {wheelfile.name}...")
                with briefcase_css_path.open("a", encoding="utf-8") as css_file:
                    self._process_wheel(wheelfile, css_file=css_file)

        return {}


class HTTPHandler(SimpleHTTPRequestHandler):
    """Convert any HTTP request into a path request on the static content folder."""

    def translate_path(self, path):
        return str(self.server.base_path / path[1:])

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


class LocalHTTPServer(ThreadingHTTPServer):
    """An HTTP server that serves local static content."""

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

    def run_app(
        self,
        app: AppConfig,
        test_mode: bool,
        passthrough: List[str],
        host,
        port,
        open_browser,
        **kwargs,
    ):
        """Start the application.

        :param app: The config object for the app
        :param test_mode: Boolean; Is the app running in test mode?
        :param passthrough: The list of arguments to pass to the app
        :param host: The host on which to run the server
        :param port: The port on which to run the server
        :param open_browser: Should a browser be opened on the newly started
            server.
        """
        if test_mode:
            raise BriefcaseCommandError("Briefcase can't run web apps in test mode.")

        self.logger.info("Starting web server...", prefix=app.app_name)

        # At least for now, there's no easy way to pass arguments to a web app.
        if passthrough:
            self.logger.warning(f"Ignoring passthrough arguments: {passthrough}")

        httpd = None
        try:
            # Create a local HTTP server
            httpd = LocalHTTPServer(
                self.project_path(app),
                host=host,
                port=port,
            )

            # Extract the host and port from the server. This is needed
            # because specifying a port of 0 lets the server pick a port.
            host, port = httpd.socket.getsockname()
            url = f"http://{host}:{port}"

            self.logger.info(f"Web server open on {url}")
            # If requested, open a browser tab on the newly opened server.
            if open_browser:
                webbrowser.open_new_tab(url)

            self.logger.info(
                "Web server log output (type CTRL-C to stop log)...",
                prefix=app.app_name,
            )
            self.logger.info("=" * 75)

            # Run the server.
            httpd.serve_forever()
        except PermissionError as e:
            if port < 1024:
                raise BriefcaseCommandError(
                    "Unable to start web server; Permission denied. Try using a port > 1023."
                ) from e
            else:
                raise BriefcaseCommandError(
                    "Unable to start web server; Permission denied. Did you specify a valid host and port?"
                ) from e
        except OSError as e:
            if e.errno in (errno.EADDRINUSE, errno.ENOSR):
                raise BriefcaseCommandError(
                    f"Unable to start web server. {host}:{port} is already in use."
                ) from e
            elif e.errno in (errno.EADDRNOTAVAIL, errno.ENOSTR):
                raise BriefcaseCommandError(
                    f"Unable to start web server. {host} is not a valid hostname."
                ) from e
            else:
                raise BriefcaseCommandError(f"Unable to start web server. {e}") from e
        except OverflowError as e:
            raise BriefcaseCommandError(
                "Unable to start web server. Port must be in the range 0-65535."
            ) from e
        except KeyboardInterrupt:
            # CTRL-C is the accepted way to stop the server.
            httpd.shutdown()
        finally:
            if httpd:
                with self.input.wait_bar("Shutting down server..."):
                    httpd.server_close()

            # Not sure why, but this is needed to mollify coverage for the
            # "test_cleanup_server_error" case. Without this pass, a missing branch
            # is reported for the "if httpd: -> exit" branch
            pass

        return {}


class StaticWebPackageCommand(StaticWebMixin, PackageCommand):
    description = "Package a static web app."

    @property
    def packaging_formats(self):
        return ["zip"]

    @property
    def default_packaging_format(self):
        return "zip"

    def package_app(self, app: AppConfig, **kwargs):
        """Package an app for distribution.

        :param app: The app to package.
        """
        self.logger.info(
            "Packaging web app for distribution...",
            prefix=app.app_name,
        )

        with self.input.wait_bar("Building archive..."):
            self.tools.shutil.make_archive(
                self.distribution_path(app).with_suffix(""),
                format="zip",
                root_dir=self.project_path(app),
            )


class StaticWebPublishCommand(StaticWebMixin, PublishCommand):
    description = "Publish a static web app."
    publication_channels = ["s3"]
    default_publication_channel = "s3"


# Declare the briefcase command bindings
create = StaticWebCreateCommand
update = StaticWebUpdateCommand
open = StaticWebOpenCommand
build = StaticWebBuildCommand
run = StaticWebRunCommand
package = StaticWebPackageCommand
publish = StaticWebPublishCommand
