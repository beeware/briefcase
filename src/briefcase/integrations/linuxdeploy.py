import hashlib
import shlex
from abc import abstractmethod
from pathlib import Path
from urllib.parse import urlparse

from requests import exceptions as requests_exceptions

from briefcase.exceptions import (
    BriefcaseCommandError,
    CorruptToolError,
    MissingToolError,
    NetworkFailure,
)

ELF_PATCH_OFFSET = 0x08
ELF_PATCH_ORIGINAL_BYTES = bytes.fromhex("414902")
ELF_PATCH_PATCHED_BYTES = bytes.fromhex("000000")


class LinuxDeployBase:
    def __init__(self, command):
        self.command = command

    @property
    @abstractmethod
    def file_name(self):
        """The name of the executable file for the tool/plugin, excluding the
        path."""
        ...  # pragma: no cover

    @property
    @abstractmethod
    def download_url(self):
        """The URL where the tool/plugin can be downloaded."""
        ...  # pragma: no cover

    @property
    @abstractmethod
    def file_path(self):
        """The folder on the local filesystem that contains the file_name."""
        ...  # pragma: no cover

    def exists(self):
        return (self.file_path / self.file_name).exists()

    def install(self):
        """Download and install linuxdeploy or plugin."""
        try:
            download_path = self.command.download_url(
                url=self.download_url,
                download_path=self.file_path,
            )
        except requests_exceptions.ConnectionError as e:
            raise NetworkFailure(f"download {self.full_name}") from e

        with self.command.input.wait_bar(f"Installing {self.full_name}..."):
            self.command.os.chmod(download_path, 0o755)
            if self.file_name.endswith("AppImage"):
                self.patch_elf_header()

    @classmethod
    def verify(cls, command, install=True, **kwargs):
        """Verify that linuxdeploy tool or plugin is available.

        :param command: The command that needs to use linuxdeploy
        :param install: Should the tool/plugin be installed if it is not found?
        :param kwargs: Any additional keyword arguments that should be passed
            to the tool at time of construction.
        :returns: A valid tool wrapper. If the tool/plugin is not
            available, and was not installed, raises MissingToolError.
        """
        tool = cls(command, **kwargs)
        if not tool.exists():
            if install:
                command.logger.info(
                    cls.install_msg.format(full_name=cls.full_name),
                    prefix="linuxdeploy",
                )
                tool.install()
            else:
                raise MissingToolError(cls.name)

        return tool

    def uninstall(self):
        """Uninstall tool."""
        with self.command.input.wait_bar(f"Removing old {self.full_name} install..."):
            (self.file_path / self.file_name).unlink()

    def upgrade(self):
        """Upgrade an existing linuxdeploy install."""
        if not self.exists():
            raise MissingToolError(self.name)

        self.uninstall()
        self.install()

    def patch_elf_header(self):
        """Patch the ELF header of the AppImage to ensure it's always
        executable.

        This patch is necessary on Linux hosts that use AppImageLauncher.
        AppImages use a modified ELF binary header starting at offset 0x08
        for additional identification. If a system has AppImageLauncher,
        the Linux kernel module `binfmt-misc` will try to load the AppImage
        with AppImageLauncher. As this binary does not exist in the Docker
        container context, we patch the ELF header of linuxdeploy to remove
        the AppImage bits, thus making all systems treat it like a regular
        ELF binary.

        Citations:
        - https://github.com/AppImage/AppImageKit/issues/1027#issuecomment-1028232809
        - https://github.com/AppImage/AppImageKit/issues/828
        """
        with (self.file_path / self.file_name).open("r+b") as appimage:
            appimage.seek(ELF_PATCH_OFFSET)
            # Check if the header at the offset is the original value
            # If so, patch it.
            if appimage.read(len(ELF_PATCH_ORIGINAL_BYTES)) == ELF_PATCH_ORIGINAL_BYTES:
                appimage.seek(ELF_PATCH_OFFSET)
                appimage.write(ELF_PATCH_PATCHED_BYTES)
                appimage.flush()
                appimage.seek(0)
                self.command.logger.info("Patched ELF header of linuxdeploy AppImage.")
            # Else if the header is the patched value, do nothing.
            elif (
                appimage.read(len(ELF_PATCH_ORIGINAL_BYTES)) == ELF_PATCH_PATCHED_BYTES
            ):
                self.command.logger.info(
                    "ELF header of linuxdeploy AppImage is already patched."
                )
            else:
                # We should only get here if the file at the AppImage patch doesn't have
                # the original or patched value. If this is the case, the file is likely
                # wrong and we should raise an exception.
                raise CorruptToolError(self.name)


class LinuxDeployPluginBase(LinuxDeployBase):
    """Base class for linuxdeploy plugins."""

    install_msg = "{full_name} was not found; downloading and installing..."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.env = {}

        if not self.file_name.startswith("linuxdeploy-plugin-"):
            raise BriefcaseCommandError(f"{self.file_name} is not a linuxdeploy plugin")

    @property
    def plugin_id(self):
        return self.file_name.split(".")[0].split("-")[2]

    @property
    def file_path(self):
        return self.command.tools_path / "linuxdeploy_plugins" / self.plugin_id


class LinuxDeployGtkPlugin(LinuxDeployPluginBase):
    full_name = "linuxdeploy GTK plugin"

    @property
    def file_name(self):
        return "linuxdeploy-plugin-gtk.sh"

    @property
    def download_url(self):
        return (
            "https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/"
            f"master/{self.file_name}"
        )


class LinuxDeployQtPlugin(LinuxDeployPluginBase):
    full_name = "linuxdeploy Qt plugin"

    @property
    def file_name(self):
        return f"linuxdeploy-plugin-qt-{self.command.host_arch}.AppImage"

    @property
    def download_url(self):
        return (
            "https://github.com/linuxdeploy/linuxdeploy-plugin-qt/"
            f"releases/download/continuous/{self.file_name}"
        )


class LinuxDeployLocalFilePlugin(LinuxDeployPluginBase):
    full_name = "user-provided linuxdeploy plugin from local file"
    install_msg = "Copying user-provided plugin into project"

    def __init__(self, command, plugin_path, bundle_path):
        self._file_name = plugin_path.name
        self.local_path = plugin_path.parent
        self._file_path = bundle_path

        # Call the super last to ensure validation of the filename
        super().__init__(command)

    @property
    def file_name(self):
        return self._file_name

    @property
    def file_path(self):
        return self._file_path

    @property
    def download_url(self):
        raise RuntimeError("Shouldn't be trying to download a local file plugin")

    def install(self):
        # Install the plugin by copying from the local path to the bundle
        # folder. This is required to ensure that the file is available inside
        # the Docker context.
        try:
            self.command.shutil.copy(
                self.local_path / self.file_name,
                self.file_path / self.file_name,
            )
        except FileNotFoundError:
            raise BriefcaseCommandError(
                f"Could not locate linuxdeploy plugin {self.local_path / self.file_name}. "
                "Is the path correct?"
            )


class LinuxDeployURLPlugin(LinuxDeployPluginBase):
    full_name = "user-provided linuxdeploy plugin from URL"

    def __init__(self, command, url):
        self._download_url = url

        url_parts = urlparse(url)
        self._file_name = url_parts.path.split("/")[-1]

        # Build a hash of the download URL; this hash is used to
        # idenfity plugins downloaded from different sources. We don't
        # just use the domain, because we need:
        #  * http://example.com/release/linuxdeploy-plugin-foobar.sh
        #  * http://example.com/dev/linuxdeploy-plugin-foobar.sh
        #  * http://example.com/archive/linuxdeploy-plugin-foobar.sh?version=1
        # to hash as different plugins, because we lose the path/query
        # component when we cache the plugin locally.
        self.hash = hashlib.sha256(url.encode("utf-8"))

        # Call the super last to ensure validation of the filename
        super().__init__(command)

    @property
    def file_name(self):
        return self._file_name

    @property
    def file_path(self):
        return (
            self.command.tools_path
            / "linuxdeploy_plugins"
            / self.plugin_id
            / self.hash.hexdigest()
        )

    @property
    def download_url(self):
        return self._download_url


class LinuxDeploy(LinuxDeployBase):
    name = "linuxdeploy"
    full_name = "linuxdeploy"
    install_msg = "linuxdeploy was not found; downloading and installing..."

    @property
    def managed_install(self):
        return True

    @property
    def file_path(self):
        return self.command.tools_path

    @property
    def file_name(self):
        return f"linuxdeploy-{self.command.host_arch}.AppImage"

    @property
    def download_url(self):
        return (
            "https://github.com/linuxdeploy/linuxdeploy/"
            f"releases/download/continuous/{self.file_name}"
        )

    @property
    def plugins(self):
        """The known linuxdeploy plugins."""
        return {
            "gtk": LinuxDeployGtkPlugin,
            "qt": LinuxDeployQtPlugin,
        }

    def verify_plugins(self, plugin_definitions, bundle_path):
        """Verify that all the declared plugin dependencies are available.

        Each plugin definition is a string, and can be:
         * The name of a known plugin (gtk, qt)
         * A URL
         * A local file.

        This definition can be preceeded by environment variables that must
        exist in the environment. For example, a plugin definition of:

            DEPLOY_GTK_VERSION=3 FOO='bar whiz' gtk

        would specify the known GTK plugin, adding `DEPLOY_GTK_VERSION` and
        `FOO` in the environment. The definition will be split the same way as
        shell arguments, so spaces should be escaped.

        :param plugin_definitions: A list of strings defining the required
            plugins.
        :param bundle_path: The location of the app bundle that requires the
            plugins.
        :returns: A dictionary of plugin ID->instantiated plugin instances.
        """
        plugins = {}
        for plugin_definition in plugin_definitions:
            # Split the plugin definition lexically.
            # The last element is the plugin ID.
            plugin_definition_parts = shlex.split(plugin_definition)
            plugin_name = plugin_definition_parts[-1]

            try:
                plugin_klass = self.plugins[plugin_name]
                self.command.logger.info(f"Using default {plugin_name} plugin")

                plugin = plugin_klass.verify(self.command)
            except KeyError:
                if plugin_name.startswith(("https://", "http://")):
                    self.command.logger.info(f"Using URL plugin {plugin_name}")
                    plugin = LinuxDeployURLPlugin.verify(self.command, url=plugin_name)
                else:
                    self.command.logger.info(f"Using local file plugin {plugin_name}")
                    plugin = LinuxDeployLocalFilePlugin.verify(
                        self.command,
                        plugin_path=Path(plugin_name),
                        bundle_path=bundle_path,
                    )

            # Preserve the environment declarations required by the plugin.
            for part in plugin_definition_parts[:-1]:
                try:
                    var, value = part.split("=", 1)
                    plugin.env[var] = value
                except ValueError:
                    # `export FOO` is valid, if unusual
                    plugin.env[part] = ""

            plugins[plugin.plugin_id] = plugin

        return plugins
