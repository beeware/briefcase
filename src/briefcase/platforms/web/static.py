import errno
import re
import subprocess
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any, List
from zipfile import ZipFile

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no-cover-if-gte-py310
    import tomli as tomllib

import tomli_w

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no-cover-if-lt-py312
    # TODO: Playwright doesn't support Python 3.12 yet.
    sync_playwright = None

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    OpenCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.commands.run import LogFilter
from briefcase.config import AppConfig
from briefcase.console import Log
from briefcase.exceptions import (
    BriefcaseCommandError,
    BriefcaseConfigError,
    BriefcaseTestSuiteFailure,
)
from briefcase.integrations.subprocess import StopStreaming


class StaticWebMixin:
    output_format = "static"
    platform = "web"

    def project_path(self, app):
        return self.bundle_path(app) / "www"

    def binary_path(self, app):
        return self.bundle_path(app) / "www" / "index.html"

    def static_path(self, app):
        return self.project_path(app) / "static"

    def wheel_path(self, app):
        return self.static_path(app) / "wheels"

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

    def _process_wheel(self, wheelfile, inserts, static_path):
        """Process a wheel, extracting any content that needs to be compiled into the
        final project.

        Extracted content comes in two forms:
        * inserts - pieces of content that will be inserted into existing files
        * static - content that will be copied wholesale. Any content in a ``static``
          folder inside the wheel will be copied as-is to the static folder,
          namespaced by the package name of the wheel.

        Any pre-existing static content for the wheel will be deleted.

        :param wheelfile: The path to the wheel file to be processed.
        :param inserts: The inserts collection for the app
        :param static_path: The location where static content should be unpacked
        """
        parts = wheelfile.name.split("-")
        package_name = parts[0]
        package_version = parts[1]
        package_key = f"{package_name} {package_version}"

        # Purge any existing extracted static files
        if (static_path / package_name).exists():
            self.tools.shutil.rmtree(static_path / package_name)

        with ZipFile(wheelfile) as wheel:
            for filename in wheel.namelist():
                path = Path(filename)
                if len(path.parts) > 1:
                    if path.parts[1] == "inserts":
                        source = str(Path(*path.parts[2:]))
                        content = wheel.read(filename).decode("utf-8")
                        if ":" in path.name:
                            target, insert = source.split(":")
                            self.logger.info(
                                f"    {source}: Adding {insert} insert for {target}"
                            )
                        else:
                            target = path.suffix[1:].upper()
                            insert = source
                            self.logger.info(f"    {source}: Adding {target} insert")

                        inserts.setdefault(target, {}).setdefault(insert, {})[
                            package_key
                        ] = content

                    elif path.parts[1] == "static":
                        content = wheel.read(filename)
                        outfilename = static_path / package_name / Path(*path.parts[2:])
                        outfilename.parent.mkdir(parents=True, exist_ok=True)
                        with outfilename.open("wb") as f:
                            f.write(content)

    def _write_pyscript_toml(self, app: AppConfig):
        """Write the ``pyscript.toml`` file for the app.

        :param app: The application whose ``pyscript.toml`` is being written.
        """
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

    def _base_inserts(self, app: AppConfig, test_mode: bool):
        """Construct the initial runtime inserts for the app.

        This adds:
        * A bootstrap script for  ``index.html`` to start the app

        :param app: The app whose base inserts we need.
        :param test_mode: Boolean; Is the app running in test mode?
        :returns: A dictionary containing the initial inserts
        """
        # Construct the bootstrap script.
        bootstrap = [
            "import runpy",
            "",
            f"# Run {app.formal_name}'s main module",
            f'runpy.run_module("{app.module_name}", run_name="__main__", alter_sys=True)',
        ]
        if test_mode:
            bootstrap.extend(
                [
                    "",
                    f"# Run {app.formal_name}'s test module",
                    f'runpy.run_module("tests.{app.module_name}", run_name="__main__", alter_sys=True)',
                ]
            )

        return {
            "index.html": {
                "bootstrap": {
                    "Briefcase": "\n".join(bootstrap),
                }
            }
        }

    def _merge_insert_content(self, inserts, key, path):
        """Merge multi-file insert content into a single insert.

        Rewrites the inserts, removing the entry for ``key``,
        producing a merged entry for ``path`` that has a single
        ``key`` insert.

        This is used to merge multiple contributed CSS files into
        a single CSS insert.

        :param inserts: The full set of inserts
        :param key: The key to merge
        :param path: The path for the merged insert.
        """
        try:
            original = inserts.pop(key)
        except KeyError:
            # Nothing to merge.
            pass
        else:
            merged = {}
            for filename, package_inserts in original.items():
                for package, css in package_inserts.items():
                    try:
                        old_css = merged[package]
                    except KeyError:
                        old_css = ""

                    full_css = f"{old_css}/********** {filename} **********/\n{css}\n"
                    merged[package] = full_css

            # Preserve the merged content as a single insert
            inserts[path] = {key: merged}

    def _write_inserts(self, app: AppConfig, filename: Path, inserts: dict):
        """Write inserts into an existing file.

        This looks for start and end markers in the named file, and replaces the
        content inside those markers with the inserted content.

        Multiple formats of insert marker are inspected, to accomodate HTML,
        Python and CSS/JS comment conventions:
        * HTML: ``<!-----@ insert:start @----->`` and ``<!-----@ insert:end @----->``
        * Python: ``#####@ insert:start @#####\n`` and ``######@ insert:end @#####\n``
        * CSS/JS: ``/*****@ insert:end @*****/`` and  ``/*****@ insert:end @*****/``

        :param app: The application whose ``pyscript.toml`` is being written.
        :param filename: The file whose insert is to be written.
        :param inserts: The inserts for the file. A 2 level dictionary, keyed by
            the name of the insert to add, and then package that contributed the
            insert.
        """
        # Read the current content
        with (self.project_path(app) / filename).open() as f:
            content = f.read()

        for insert, packages in inserts.items():
            for comment, marker, replacement in [
                # HTML
                (
                    (
                        "<!--------------------------------------------------\n"
                        " * {package}\n"
                        " -------------------------------------------------->\n"
                        "{content}"
                    ),
                    r"<!-----@ {insert}:start @----->.*?<!-----@ {insert}:end @----->",
                    r"<!-----@ {insert}:start @----->\n{content}<!-----@ {insert}:end @----->",
                ),
                # CSS/JS
                (
                    (
                        "/**************************************************\n"
                        " * {package}\n"
                        " *************************************************/\n"
                        "{content}"
                    ),
                    r"/\*\*\*\*\*@ {insert}:start @\*\*\*\*\*/.*?/\*\*\*\*\*@ {insert}:end @\*\*\*\*\*/",
                    r"/*****@ {insert}:start @*****/\n{content}/*****@ {insert}:end @*****/",
                ),
                # Python
                (
                    (
                        "##################################################\n"
                        "# {package}\n"
                        "##################################################\n"
                        "{content}"
                    ),
                    r"#####@ {insert}:start @#####\n.*?#####@ {insert}:end @#####",
                    r"#####@ {insert}:start @#####\n{content}\n#####@ {insert}:end @#####",
                ),
            ]:
                full_insert = "\n".join(
                    comment.format(package=package, content=content)
                    for package, content in packages.items()
                )
                content = re.sub(
                    marker.format(insert=insert),
                    replacement.format(insert=insert, content=full_insert),
                    content,
                    flags=re.MULTILINE | re.DOTALL,
                )

        # Write the new index.html
        with (self.project_path(app) / filename).open("w") as f:
            f.write(content)

    def build_app(self, app: AppConfig, test_mode: bool = False, **kwargs):
        """Build the static web deployment for the application.

        :param app: The application to build
        :param test_mode: Boolean; Is the app running in test mode?
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
            self._write_pyscript_toml(app)

        inserts = self._base_inserts(app, test_mode=test_mode)

        self.logger.info("Compile contributed content from wheels")
        with self.input.wait_bar("Compiling contributed content from wheels..."):
            # Extract insert and static resources from packaged wheels
            for wheelfile in sorted(self.wheel_path(app).glob("*.whl")):
                self.logger.info(f"  Processing {wheelfile.name}...")
                self._process_wheel(
                    wheelfile,
                    inserts=inserts,
                    static_path=self.static_path(app),
                )

        # Reorganize CSS content so that there's a single content insert
        # for all contributed packages
        self._merge_insert_content(inserts, "CSS", "static/css/briefcase.css")

        # Add content inserts to the site content.
        self.logger.info("Add content inserts")
        with self.input.wait_bar("Adding content inserts..."):
            for filename, file_inserts in inserts.items():
                self.logger.info(f"  Processing {filename}...")
                self._write_inserts(app, filename=filename, inserts=file_inserts)

        return {}


class HTTPHandler(SimpleHTTPRequestHandler):
    """Convert any HTTP request into a path request on the static content folder."""

    server: "LocalHTTPServer"

    def translate_path(self, path):
        return str(self.server.base_path / path[1:])

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    # Strip out ANSI escape sequences from messages. This was added in security releases
    # before Python 3.12.
    _control_char_table = str.maketrans(
        {c: rf"\x{c:02x}" for c in [*range(0x20), *range(0x7F, 0xA0)]}
    )
    _control_char_table[ord("\\")] = r"\\"

    def log_message(self, format: str, *args: Any) -> None:
        message = (format % args).translate(self._control_char_table)
        if self.server.logger:
            self.server.logger.info(
                f"{self.address_string()} - - [{self.log_date_time_string()}] {message}"
            )


class LocalHTTPServer(ThreadingHTTPServer):
    """An HTTP server that serves local static content."""

    def __init__(
        self,
        base_path,
        host,
        port,
        RequestHandlerClass=HTTPHandler,
        *,
        logger: Log,
    ):
        self.base_path = base_path
        self.logger = logger
        super().__init__((host, port), RequestHandlerClass)


class StaticWebRunCommand(StaticWebMixin, RunCommand):
    description = "Run a static web project."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.playwright = sync_playwright

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
        self.logger.info("Starting web server...", prefix=app.app_name)

        # At least for now, there's no easy way to pass arguments to a web app.
        if passthrough:
            self.logger.warning(f"Ignoring passthrough arguments: {passthrough}")

        httpd = None
        try:
            # Create a local HTTP server.
            # Don't log the server if we're in test mode;
            # otherwise, log server activity to the console
            httpd = LocalHTTPServer(
                self.project_path(app),
                host=host,
                port=port,
                logger=None if test_mode else self.logger,
            )

            # Extract the host and port from the server. This is needed
            # because specifying a port of 0 lets the server pick a port.
            host, port = httpd.socket.getsockname()
            url = f"http://{host}:{port}"

            if test_mode:
                # Ensure that the Chromium Playwright browser is installed
                # This is a no-output, near no-op if the browser *is* installed;
                # If it isn't, it shows a download progress bar.
                self.tools.subprocess.run(
                    ["playwright", "install", "chromium"],
                    stream_output=False,
                )

                # Start the web server in a background thread
                server_thread = Thread(target=httpd.serve_forever)
                server_thread.start()

                self.logger.info("Running test suite...")
                self.logger.info("=" * 75)

                # Open a Playwright session
                with self.playwright() as playwright:
                    browser = playwright.chromium.launch(headless=not open_browser)
                    page = browser.new_page()

                    # Install a handler that will capture every line of
                    # log content in a buffer.
                    buffer = []
                    page.on("console", lambda msg: buffer.append(msg.text))

                    # Load the test page.
                    page.goto(url)

                    # Build a log filter looking for test suite termination
                    log_filter = LogFilter(
                        clean_filter=None,
                        clean_output=True,
                        exit_filter=LogFilter.test_filter(
                            getattr(app, "exit_regex", LogFilter.DEFAULT_EXIT_REGEX)
                        ),
                    )
                    try:
                        while True:
                            # Process all the lines in the accumulated log buffer,
                            # looking for the termination condition. Finding the
                            # termination condition is what stops the test suite.
                            for line in buffer:
                                for filtered in log_filter(line):
                                    self.logger.info(filtered)
                            buffer = []

                            # Insert a short pause so that Playwright can
                            # generate the next batch of console logs
                            page.wait_for_timeout(100)
                    except StopStreaming:
                        if log_filter.returncode == 0:
                            self.logger.info("Test suite passed!", prefix=app.app_name)
                        else:
                            if log_filter.returncode is None:
                                raise BriefcaseCommandError(
                                    "Test suite didn't report a result."
                                )
                            else:
                                self.logger.error(
                                    "Test suite failed!", prefix=app.app_name
                                )
                                raise BriefcaseTestSuiteFailure()
                    finally:
                        # Close the Playwright browser, and shut down the web server
                        browser.close()
                        httpd.shutdown()
            else:
                # Normal execution mode
                self.logger.info(f"Web server open on {url}")

                # If requested, open a browser tab on the newly opened server.
                if open_browser:
                    webbrowser.open_new_tab(url)

                self.logger.info(
                    "Web server log output (type CTRL-C to stop log)...",
                    prefix=app.app_name,
                )
                self.logger.info("=" * 75)

                # Start the web server in blocking mode.
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
