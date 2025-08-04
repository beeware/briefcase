import errno
import shutil
import subprocess
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from typing import Any
from zipfile import ZipFile

from briefcase.console import Console
from briefcase.exceptions import (
    BriefcaseCommandError,
    BriefcaseConfigError,
    UnsupportedCommandError,
)

if sys.version_info >= (3, 11):  # pragma: no-cover-if-lt-py311
    import tomllib
else:  # pragma: no-cover-if-gte-py311
    import tomli as tomllib

import tomli_w

from briefcase.commands import (
    BuildCommand,
    CreateCommand,
    DevCommand,
    OpenCommand,
    PackageCommand,
    PublishCommand,
    RunCommand,
    UpdateCommand,
)
from briefcase.config import AppConfig


class StaticWebMixin:
    output_format = "static"
    platform = "web"
    platform_target_version = "0.3.21"

    def project_path(self, app):
        return self.bundle_path(app) / "www"

    def binary_path(self, app):
        return self.bundle_path(app) / "www/index.html"

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

    def _trim_file(self, path, sentinel):
        """Re-write a file to strip any content after a sentinel line.

        The file is stored in-memory, so it shouldn't be used on files with a *lot* of
        content before the sentinel.

        :param path: The path to the file to be trimmed
        :param sentinel: The content of the sentinel line. This will become the last
            line in the trimmed file.
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
        :param inserts: The insert collection of html for the app
        :param static_path: The location where static content should be unpacked
        """
        parts = wheelfile.name.split("-")
        package_name = parts[0]
        package_version = parts[1]
        package_key = f"{package_name} {package_version}"

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
                                f"  {source}: Adding {insert} insert for {target}"
                            )
                        else:
                            target = path.suffix[1:].upper()
                            insert = source
                            self.logger.info(f"    {source}: Adding {target} insert")

                        insert.setdefault(target, {}).setdefault(insert, {})[
                            
                        ]

    def _gather_backend_config(self, wheels):
        """Processes multiple wheels to gather a config.toml and a base pyscript.toml file.

        :param wheels: A list of wheel files to be scanned.
        """
        config_counter = 0
        pyscript_config = None

        for wheelfile in wheels:
            with ZipFile(wheelfile) as wheel:
                for filename in wheel.namelist():
                    path = Path(filename)
                    if (
                        len(path.parts) > 1
                        and path.parts[1] == "deploy"
                        and path.name == "config.toml"
                    ):
                        self.console.info(f"    Found {filename}")
                        config_counter += 1
                        # Raise an error if more than one configuration file is supplied.
                        if config_counter > 1:
                            raise BriefcaseConfigError(
                                "Only 1 backend configuration file can be supplied."
                            )
                        # Check which backend type is used. Raise error if no backend is present in config.toml
                        with wheel.open(filename) as config_file:
                            config_data = tomllib.load(config_file)

                            if "backend" in config_data:
                                backend = config_data.get("backend")

                                # Currently, only pyscript is supported, will raise an error if another backend is found.
                                if backend != "pyscript":
                                    raise BriefcaseConfigError(
                                        "Only 'pyscript' backend is currently supported for web static builds."
                                    )

                                pyscript_config = self._gather_backend_config_file(wheel, backend, path)

                            else:
                                raise BriefcaseConfigError(
                                    'No backend was provided in config.toml file.'
                                )
        # Return a blank pyscript config if no configuration file is found.
        if (
            config_counter == 0
            and pyscript_config is None
        ):
            pyscript_config = {}

        return pyscript_config

    def _gather_backend_config_file(self, wheel, backend, path):
        """Find backend config file (eg: pyscript.toml) from a wheel and save it to project pyscript.toml if found.

        :param wheel: Wheel file to scan for configuration file.
        :param backend: The backend type as a String (eg "pyscript")
        :param path: Path to the wheels configuration file (config.toml). This should be in the same directory as the backend configuration file.
        """
        backend_counter = 0
        backend_config = None
        deploy_dir = path.parent

        for deploy_file in wheel.namelist():
            deploy_parent = Path(deploy_file).parent
            if (
                deploy_parent == deploy_dir
                and Path(deploy_file).name == f"{backend}.toml"
            ):
                backend_counter += 1
                # Raise an error if more than one pyscript.toml file is found.
                if backend_counter > 1:
                    raise BriefcaseConfigError(
                        "Only 1 pyscript configuration file can be supplied."
                    )
                # Save pyscript config file.
                else:
                    try:
                        with wheel.open(deploy_file) as pyscript_file:
                            backend_config = tomllib.load(pyscript_file)
                    except tomllib.TOMLDecodeError as e:
                        raise BriefcaseConfigError(
                            f"pyscript.toml content isn't valid TOML: {e}"
                        ) from e
        return backend_config

    def build_app(self, app: AppConfig, **kwargs):
        """Build the static web deployment for the application.

        :param app: The application to build
        """
        self.console.info("Building web project...", prefix=app.app_name)

        # deploy_path = files("toga_web.deploy")
        # deploy_config_path = deploy_path / "config.toml"
        # deploy_pyscript_path = deploy_path / "pyscript.toml"

        # if deploy_config_path.exists():
        #     try:
        #         with deploy_config_path.open("rb") as f:
        #             deploy_config = tomllib.load(f)
        #     except tomllib.TOMLDecodeError as e:
        #         raise BriefcaseConfigError(f"Invalid config.toml: {e}") from e
        # else:
        #     deploy_config = {}

        # if "backend" in deploy_config and deploy_config["backend"] != "pyscript":
        #     raise BriefcaseConfigError(
        #         "Only 'pyscript' backend is currently supported for web static builds."
        #     )

        # if deploy_pyscript_path.exists():
        #     try:
        #         extra_pyscript_toml = deploy_pyscript_path.read_text(encoding="utf-8")
        #     except Exception as e:
        #         raise BriefcaseConfigError(
        #             f"Unable to read deploy/pyscript.toml: {e}"
        #         ) from e
        # else:
        #     extra_pyscript_toml = ""

        if self.wheel_path(app).exists():
            with self.console.wait_bar("Removing old wheels..."):
                self.tools.shutil.rmtree(self.wheel_path(app))

        self.wheel_path(app).mkdir(parents=True)

        with self.console.wait_bar("Building app wheel..."):
            try:
                self.tools.subprocess.run(
                    [
                        sys.executable,
                        "-u",
                        "-X",
                        "utf8",
                        "-m",
                        "wheel",
                        "pack",
                        self.app_path(app),
                        "--dest-dir",
                        self.wheel_path(app),
                    ],
                    check=True,
                    encoding="UTF-8",
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to build wheel for app {app.app_name!r}"
                ) from e

        with self.console.wait_bar("Installing wheels for requirements..."):
            try:
                self.tools.subprocess.run(
                    [
                        sys.executable,
                        "-u",
                        "-X",
                        "utf8",
                        "-m",
                        "pip",
                        "wheel",
                        "--wheel-dir",
                        self.wheel_path(app),
                        "-r",
                        self.bundle_path(app) / "requirements.txt",
                    ]
                    + (["-vv"] if self.console.is_deep_debug else []),
                    check=True,
                    encoding="UTF-8",
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Unable to install requirements for app {app.app_name!r}"
                ) from e

        with self.console.wait_bar("Writing Pyscript configuration file..."):
            # Load any pre-existing pyscript.toml provided by the template. If the file
            # doesn't exist, assume an empty pyscript.toml as a starting point.
            config = self._gather_backend_config(self.wheel_path(app).glob("*.whl"))

            # Add the packages declaration to the existing pyscript.toml.
            # Ensure that we're using Unix path separators, as the content
            # will be parsed by pyscript in the browser.
            config["packages"] = [
                f"/{'/'.join(wheel.relative_to(self.project_path(app)).parts)}"
                for wheel in sorted(self.wheel_path(app).glob("*.whl"))
            ]

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

            # # Parse any deploy pyscript.toml content, and merge it into
            # # the overall content
            # try:
            #     extra = tomllib.loads(extra_pyscript_toml)
            #     config.update(extra)
            # except tomllib.TOMLDecodeError as e:
            #     raise BriefcaseConfigError(
            #         f"Deploy pyscript.toml content isn't valid TOML: {e}"
            #     ) from e
            # except AttributeError:
            #     pass

            # Write the final configuration.
            with (self.project_path(app) / "pyscript.toml").open("wb") as f:
                tomli_w.dump(config, f)

        self.console.info("Compile static web content from wheels")
        with self.console.wait_bar("Compiling static web content from wheels..."):
            # Trim previously compiled content out of briefcase.css
            briefcase_css_path = self.project_path(app) / "static/css/briefcase.css"
            self._trim_file(
                briefcase_css_path,
                sentinel=" ******************* Wheel contributed styles **********************/",
            )

            # Extract static resources from packaged wheels
            for wheelfile in sorted(self.wheel_path(app).glob("*.whl")):
                self.console.info(f"  Processing {wheelfile.name}...")
                with briefcase_css_path.open("a", encoding="utf-8") as css_file:
                    self._process_wheel(wheelfile, css_file=css_file)

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
        logger: Console,
    ):
        self.base_path = base_path
        self.logger = logger
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
            help="Don't open a web browser on the newly opened server",
            required=False,
        )

    def run_app(
        self,
        app: AppConfig,
        passthrough: list[str],
        host,
        port,
        open_browser,
        **kwargs,
    ):
        """Start the application.

        :param app: The config object for the app
        :param passthrough: The list of arguments to pass to the app
        :param host: The host on which to run the server
        :param port: The port on which to run the server
        :param open_browser: Should a browser be opened on the newly started server.
        """
        if app.test_mode:
            raise BriefcaseCommandError("Briefcase can't run web apps in test mode.")

        self.console.info("Starting web server...", prefix=app.app_name)

        # At least for now, there's no easy way to pass arguments to a web app.
        if passthrough:
            self.console.warning(f"Ignoring passthrough arguments: {passthrough}")

        httpd = None
        try:
            # Create a local HTTP server
            try:
                httpd = LocalHTTPServer(
                    self.project_path(app),
                    host=host,
                    port=port,
                    logger=self.console,
                )
            except OSError as e:
                if e.errno in (errno.EADDRINUSE, errno.ENOSR):
                    self.console.warning(
                        f"Using a system-allocated port since port {port} is already in use. "
                        "Use -p/--port to manually specify a port."
                    )
                    httpd = LocalHTTPServer(
                        self.project_path(app),
                        host=host,
                        port=0,
                        logger=self.console,
                    )
                else:
                    raise

            # Extract the host and port from the server. This is needed
            # because specifying a port of 0 lets the server pick a port.
            host, port = httpd.socket.getsockname()
            url = f"http://{host}:{port}"

            self.console.info(f"Web server open on {url}")
            # If requested, open a browser tab on the newly opened server.
            if open_browser:
                webbrowser.open_new_tab(url)

            self.console.info(
                "Web server log output (type CTRL-C to stop log)...",
                prefix=app.app_name,
            )
            self.console.info("=" * 75)

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
            if e.errno in (errno.EADDRNOTAVAIL, errno.ENOSTR):
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
                with self.console.wait_bar("Shutting down server..."):
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
        self.console.info(
            "Packaging web app for distribution...",
            prefix=app.app_name,
        )

        with self.console.wait_bar("Building archive..."):
            self.tools.shutil.make_archive(
                self.distribution_path(app).with_suffix(""),
                format="zip",
                root_dir=self.project_path(app),
            )


class StaticWebPublishCommand(StaticWebMixin, PublishCommand):
    description = "Publish a static web app."
    publication_channels = ["s3"]
    default_publication_channel = "s3"


class StaticWebDevCommand(StaticWebMixin, DevCommand):
    description = "Run a static web project in development mode. (Work in progress)"

    def run_dev_app(self, app: AppConfig, env, passthrough=None, **kwargs):
        raise UnsupportedCommandError(
            platform="web",
            output_format="static",
            command="dev",
        )

    # implement logic to run the web server in development mode


# Declare the briefcase command bindings
create = StaticWebCreateCommand
update = StaticWebUpdateCommand
open = StaticWebOpenCommand
build = StaticWebBuildCommand
run = StaticWebRunCommand
package = StaticWebPackageCommand
publish = StaticWebPublishCommand
dev = StaticWebDevCommand
