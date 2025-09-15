import errno
import re
import subprocess
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
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

    def write_inserts(
        self, app: AppConfig, filename: Path, inserts: dict[str, dict[str, str]]
    ):
        """Write inserts into an existing file.

        This function looks for start and end markers in the named file and
        replaces the content inside the markers with the inserted content.

        Multiple formats of insert marker are inspected to accommodate HTML
        and CSS/JS comment conventions:
        * HTML: ``<!--@@ insert:start @@-->`` and ``<!--@@ insert:end @@-->``
        * CSS/JS: ``/*@@ insert:start @@*/`` and ``/*@@ insert:end @@*/``

        Inserts and package contributions are processed in sorted order to ensure deterministic builds.

        :param app: The application whose ``pyscript.toml`` is being written.
        :param filename: The file whose insert is to be written.
        :param inserts: The inserts for the file. A 2 level dictionary, keyed by
            the name of the insert to add, and then package that contributed the
            insert.
        """
        # Load file content, skip if file not found
        target_path = self.project_path(app) / filename
        try:
            file_text = target_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self.console.warning(f"  Target {filename} not found; skipping inserts.")
            return

        # Each insert slot and its package contributions are processed in sorted order
        for insert, pkg_contribs in sorted(inserts.items()):
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

            # Build bodies from the same contributions
            html_body = "\n".join(
                html_banner.format(package=pkg, content=text)
                for pkg, text in sorted(pkg_contribs.items())
                if text
            )
            css_body = "\n".join(
                css_banner.format(package=pkg, content=text)
                for pkg, text in sorted(pkg_contribs.items())
                if text
            )
            body_map = {"html": html_body, "css": css_body}

            # Marker patterns for HTML and CSS/JS
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

            # Pre-compile patterns once per insert
            compiled_markers = [
                (
                    re.compile(
                        pattern_tmpl.format(insert=insert),
                        flags=re.MULTILINE | re.DOTALL,
                    ),
                    repl_tmpl,
                    kind,
                )
                for (pattern_tmpl, repl_tmpl, kind) in marker_styles
            ]

            # Apply all matching marker styles
            any_match = False
            for pattern, repl_tmpl, kind in compiled_markers:
                if pattern.search(file_text):
                    file_text = pattern.sub(
                        repl_tmpl.format(insert=insert, content=body_map.get(kind, "")),
                        file_text,
                    )
                    any_match = True

            if not any_match:
                self.console.warning(
                    f"  Slot '{insert}' markers not found in {filename}; skipping."
                )

        # Save modified content
        target_path.write_text(file_text, encoding="utf-8")

    def write_pyscript_version(
        self, app: AppConfig, filename: Path, pyscript_version: str
    ):
        """Write pyscript version into an existing html file.

        This function looks for markers in the named file and replaces the
        markers with the pyscript version.

        The markers are in pyscript declarations within the html.

        * Marker: ``<!--@@ pyscript_version @@-->``
        * Example: ``<link rel="stylesheet" href="https://pyscript.net/releases/<!--@@ pyscript_version @@-->/core.css">``

        Pyscript versions are processed in sorted order to ensure deterministic builds.

        :param app: The application being written.
        :param filename: The html file whose pyscript version is to be written.
        :param pyscript_version: The pyscript version number to be inserted.
        """
        # Load file content, skip if file not found
        target_path = self.project_path(app) / filename
        try:
            file_text = target_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise BriefcaseConfigError(
                f"{filename} not found; pyscript version could not be inserted."
            )

        marker = r"<!--@@ PyScript:start @@-->.*<!--@@ PyScript:end @@-->"
        insertion = f"""<!--@@ PyScript:start @@-->
        <script type="module">
            // Hide the splash screen when the page is ready.
            import {{ hooks }} from "https://pyscript.net/releases/{pyscript_version}/core.js";
            hooks.main.onReady.add(() => {{
                document.getElementById("briefcase-splash").classList.add("hidden");
            }});
        </script>

        <link rel="stylesheet" href="https://pyscript.net/releases/{pyscript_version}/core.css">
        <script type="module" src="https://pyscript.net/releases/{pyscript_version}/core.js"></script>
        <!--@@ PyScript:end @@-->"""
        insertion = insertion.replace("pyscript_version", pyscript_version)
        if re.search(marker, file_text, flags=re.DOTALL):
            file_text = re.sub(marker, insertion, file_text, flags=re.DOTALL)
        else:
            raise BriefcaseConfigError(
                f"No pyscript markers found in {filename}; pyscript may not be configured correctly."
            )

        target_path.write_text(file_text, encoding="utf-8")

    def _process_wheel(
        self,
        wheelfile,
        inserts: dict[str, dict[str, dict[str, str]]],
    ):
        """Process a wheel to collect insert and style content for the final project.

        Scans the wheel for:
        * Legacy CSS – `.css` files under ``static/`` are appended to the
        ``briefcase.css`` insert slot with a deprecation warning.
        * HTML inserts – HTML header files under ``deploy/inserts/<insert>.<target>``
        are added to the corresponding insert slot for the target file.
        * CSS inserts – Any `.css` under ``deploy/inserts/`` is appended to
        the ``briefcase.css`` insert slot.

        Inserts are grouped by ``<package_name> <version>`` for ordering and
        provenance. All content must be UTF-8 encoded.

        :param wheelfile: Path to the wheel file.
        :param inserts: Nested dict of inserts keyed by target - insert - package.
        :param static_path: Path for static content.
        """
        name_parts = wheelfile.name.split("-")
        package_key = f"{name_parts[0]} {name_parts[1]}"

        # Warning flag for legacy CSS
        legacy_css_warning = False

        with ZipFile(wheelfile) as wheel:
            for filename in sorted(wheel.namelist()):
                # Skip directories and shallow paths
                path = Path(filename)
                parts = path.parts

                # Legacy CSS handling
                if (
                    len(parts) > 1
                    and parts[1] == "static"
                    and path.suffix.lower() == ".css"
                ):
                    self.console.info(f"    Found {filename}")

                    # Show deprecation warning once per wheel
                    if not legacy_css_warning:
                        self.console.warning(
                            f"    {wheelfile.name}: legacy '/static' CSS detected; "
                            "treating as insert into briefcase.css; this legacy handling will be removed in the future."
                        )
                        legacy_css_warning = True

                    try:
                        css_text = wheel.read(filename).decode("utf-8")
                    except UnicodeDecodeError as e:
                        raise BriefcaseCommandError(
                            f"{filename}: CSS content must be UTF-8 encoded"
                        ) from e

                    rel_inside = "/".join(path.parts[2:])
                    contrib_key = f"{package_key} (legacy static CSS: {rel_inside})"

                    # Add CSS content to briefcase.css insert slot
                    target = "static/css/briefcase.css"
                    insert = "CSS"
                    pkg_map = inserts.setdefault(target, {}).setdefault(insert, {})
                    pkg_map[contrib_key] = css_text

                # New deploy/inserts handling
                elif len(parts) >= 3 and parts[1] == "deploy" and parts[2] == "inserts":
                    self.console.info(f"    Found {filename}")
                    basename = parts[-1]

                    # HTML/other inserts
                    if not basename.endswith(".css"):
                        try:
                            # Split filename into <insert> slot and <target>
                            insert, target = basename.split(".", 1)
                            self.console.info(
                                f"    {filename}: Adding {insert} insert for {target}"
                            )
                            try:
                                text = wheel.read(filename).decode("utf-8")
                            except UnicodeDecodeError as e:
                                raise BriefcaseCommandError(
                                    f"{filename}: insert must be UTF-8 encoded"
                                ) from e

                            # Store insert under the correct target and slot
                            pkg_map = inserts.setdefault(target, {}).setdefault(
                                insert, {}
                            )
                            # Append if package already contributed to this slot
                            if package_key in pkg_map and pkg_map[package_key]:
                                pkg_map[package_key] += "\n" + text
                            else:
                                pkg_map[package_key] = text

                        except ValueError:
                            self.console.debug(
                                f"    {filename}: not an <insert>.<target> name; skipping generic insert handling."
                            )

                    # CSS inserts
                    if basename.endswith(".css"):
                        try:
                            css_text = wheel.read(filename).decode("utf-8")
                        except UnicodeDecodeError as e:
                            raise BriefcaseCommandError(
                                f"{filename}: insert must be UTF-8 encoded"
                            ) from e

                        # Wrap CSS with a source banner showing package and file
                        rel_inside = "/".join(parts[3:]) or basename
                        contrib_key = f"{package_key} (deploy CSS: {rel_inside})"

                        # Add CSS content to briefcase.css insert slot
                        target = "static/css/briefcase.css"
                        insert = "CSS"
                        pkg_map = inserts.setdefault(target, {}).setdefault(insert, {})
                        pkg_map[contrib_key] = css_text

    def extract_backend_config(self, wheels):
        """Processes multiple wheels to gather a config.toml and a base pyscript.toml
        file.

        :param wheels: A list of wheel files to be scanned.
        """
        config_package = None
        config_package_list = []
        config_filename = None
        pyscript_version = "2024.11.1"
        pyscript_config = None

        # Find packages containing a config.toml file.
        for wheelfile in wheels:
            with ZipFile(wheelfile) as wheel:
                for filename in wheel.namelist():
                    path = Path(filename)
                    if (
                        len(path.parts) == 3
                        and path.parts[1] == "deploy"
                        and path.name == "config.toml"
                    ):
                        self.console.info(f"    Found {filename}")
                        config_package_list.append(wheelfile)
                        config_filename = filename

        # Return a blank pyscript config if no configuration file is found.
        if len(config_package_list) == 0:
            pyscript_config = {}
        # Raise an error if more than one configuration file is supplied.
        elif len(config_package_list) > 1:
            raise BriefcaseConfigError(
                f"""Only 1 backend configuration file can be supplied.
                Initial config.toml found in package: {config_package}
                Duplicate config.toml found in package: {wheel.filename}"""
            )
        # Gather a backend configuration file from the package.
        # For now, is a pyscript.toml as no other backend is currently supported.
        else:
            with ZipFile(config_package_list[0]) as wheel:
                # Check which backend type is used.
                with wheel.open(config_filename) as config_file:
                    config_data = tomllib.load(config_file)

                    if "backend" in config_data:
                        backend = config_data.get("backend")

                        # Currently, only pyscript is supported, will raise an error if another backend is found.
                        if backend != "pyscript":
                            raise BriefcaseConfigError(
                                "Only 'pyscript' backend is currently supported for web static builds."
                            )

                        # Get pyscript version from config.toml. Use default if not present.

                        if "version" in config_data:
                            pyscript_version = config_data.get("version")

                        pyscript_path = config_filename.replace(
                            "config.toml", "pyscript.toml"
                        )
                        try:
                            with wheel.open(pyscript_path) as pyscript_file:
                                pyscript_config = tomllib.load(pyscript_file)
                        except KeyError:
                            raise BriefcaseConfigError(
                                f"Pyscript configuration file not found in package: {config_package_list[0]}"
                            )

                    # Raise error if no backend is present in config.toml
                    else:
                        raise BriefcaseConfigError(
                            "No backend was provided in config.toml file."
                        )

        return pyscript_config, pyscript_version

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
            config, pyscript_version = self.extract_backend_config(
                self.wheel_path(app).glob("*.whl")
            )

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

            # Write the final configuration
            with (self.project_path(app) / "pyscript.toml").open("wb") as f:
                tomli_w.dump(config, f)

        self.console.info("Compile static web content from wheels")
        with self.console.wait_bar("Compiling static web content from wheels..."):
            # Add pyscript_version to index.html
            self.write_pyscript_version(app, Path("index.html"), pyscript_version)

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
            for target, target_inserts in sorted(inserts.items()):
                self.write_inserts(app, Path(target), target_inserts)

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
