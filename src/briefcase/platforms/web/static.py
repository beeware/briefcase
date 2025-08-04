import errno
import shutil
import subprocess
import sys
import webbrowser
import re
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
        return self.static_path / "wheels"

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

    def _merge_insert_content(self, inserts, key, path):
        """Merge multi-file insert content into a single insert file.

        Rewrites the inserts, removing the entry for ``key``,
        producing a merged entry for ``path`` that has a single
        ``key`` insert.
        This is used to merge multiple contributed CSS files into
        a single CSS insert.

        :param inserts: All inserts
        :param key: The key to merge
        :param path: The path for the merge insert.
        """

        try:
            original = inserts.pop(key)
        except KeyError:
            # No merging
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

        This function looks for start and end markers in the named file and
        replaces the content inside the markers with the inserted content.

        Multiple formats of insert marker are inspected to accommodate HTML
        and CSS/JS comment conventions:
        * HTML: ``<!--@@ insert:start @@-->`` and ``<!--@@ insert:end @@-->``
        * CSS/JS: ``/*@@ insert:start @@*/`` and ``/*@@ insert:end @@*/``

        :param app: The application whose ``pyscript.toml`` is being written.
        :param filename: The file whose insert is to be written.
        :param inserts: The inserts for the file. A 2 level dictionary, keyed by
            the name of the insert to add, and then package that contributed the
            insert.
        """
        # Read the current content
        target_path = self.project_path(app) / filename
        if not target_path.exists():
            self.console.warning(f"  Target {filename} not found; skipping inserts.")
            return

        with target_path.open("r", encoding="utf-8") as f:
            file_text = f.read()

        for insert in sorted(inserts.keys()):
            packages = inserts[insert]

            html_banner = (
                "<!--------------------------------------------------\n"
                " * {package}\n"
                " -------------------------------------------------->\n"
                "{content}"
            )
            css_banner = (
                "/**************************************************\n"
                " * {package}\n"
                " *************************************************/\n"
                "{content}"
            )

            marker_styles = [
                # HTML
                (
                    r"<!--@@ {insert}:start @@-->.*?<!--@@ {insert}:end @@-->",
                    r"<!--@@ {insert}:start @@-->\n{content}<!--@@ {insert}:end @@-->",
                    "html",
                ),
                # CSS/JS
                (
                    r"/\*@@ {insert}:start @@\*/.*?/\*@@ {insert}:end @@\*/",
                    r"/*@@ {insert}:start @@*/\n{content}/*@@ {insert}:end @@*/",
                    "css",
                ),
            ]

            html_body = "\n".join(
                html_banner.format(package=pkg, content=packages[pkg])
                for pkg in sorted(packages.keys())
            )
            css_body = "\n".join(
                css_banner.format(package=pkg, content=packages[pkg])
                for pkg in sorted(packages.keys())
            )

            replaced = False
            for pattern_tmpl, repl_tmpl, kind in marker_styles:
                pattern = re.compile(
                    pattern_tmpl.format(nsert=insert), flags=re.MULTILINE | re.DOTALL
                )
                if pattern.search(file_text):
                    body = html_body if kind == "html" else css_body
                    file_text = pattern.sub(
                        repl_tmpl.format(insert=insert, content=body),
                        file_text,
                    )
                    replaced = True
                    break

            if not replaced:
                self.console.warning(
                    f"  Slot '{insert}' markers not found in {filename}; skipping."
                )

        with target_path.open("w", encoding="utf-8") as f:
            f.write(file_text)

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

        # Purge any existing extracted static files for this wheel
        pkg_static_root = static_path / package_name
        if pkg_static_root.exists():
            self.tools.shutil.rmtree(pkg_static_root)

        with ZipFile(wheelfile) as wheel:
            for filename in wheel.namelist():
                path = Path(filename)
                if len(path.parts) < 2:
                    continue

                is_inserts = (path.parts[1] == "inserts") or (
                    len(path.parts) >= 3
                    and path.parts[1] == "deploy"
                    and path.parts[2] == "inserts"
                )
                if is_inserts and path.name:
                    source = (
                        str(Path(*path.parts[2:]))
                        if path.parts[1] == "inserts"
                        else str(Path(*path.parts[3:]))
                    )
                    if ":" not in path.name:
                        self.console.warning(
                            f"    {source}: missing ':<insert>'; skipping insert."
                        )
                        continue
                    target, insert = source.split(":", 1)
                    self.console.info(
                        f"    {source}: Adding {insert} insert for {target}"
                    )
                    try:
                        text = wheel.read(filename).decode("utf-8")
                    except UnicodeDecodeError:
                        self.console.warning(
                            f"    {source}: non-UTF8 insert; skipping."
                        )
                        continue
                    inserts.setdefault(target, {}).setdefault(insert, {})[
                        package_key
                    ] = text
                    continue

                is_static = (path.parts[1] == "static") or (
                    len(path.parts) >= 3
                    and path.parts[1] == "deploy"
                    and path.parts[2] == "static"
                )
                if is_static:
                    if filename.endswith("/"):
                        continue
                    rel_parts = (
                        path.parts[2:] if path.parts[1] == "static" else path.parts[3:]
                    )
                    outfilename = pkg_static_root / Path(*rel_parts)
                    outfilename.parent.mkdir(parents=True, exist_ok=True)
                    with outfilename.open("wb") as f:
                        f.write(wheel.read(filename))

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
        """Find backend config file (eg: pyscript.toml) from a wheel and save it to
        project pyscript.toml if found.

        :param wheel: Wheel file to scan for configuration file.
        :param backend: The backend type as a String (eg "pyscript")
        :param path: Path to the wheels configuration file (config.toml). This should be
            in the same directory as the backend configuration file.
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

            inserts: dict[str, dict[str, dict[str, str]]] = {}
            static_root = self.static_path(app)

            for wheelfile in sorted(self.wheel_path(app).glob("*.whl")):
                self.console.info(f"  Processing {wheelfile.name}...")
                self._process_wheel(
                    wheelfile=wheelfile,
                    inserts=inserts,
                    static_path=static_root,
                )

            # Write inserts per target
            for target in sorted(inserts.keys()):
                self._write_inserts(app, Path(target), inserts[target])

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
