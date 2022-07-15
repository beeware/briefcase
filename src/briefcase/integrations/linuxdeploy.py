import hashlib
from abc import abstractmethod
from urllib.parse import urlparse

from requests import exceptions as requests_exceptions

from briefcase.exceptions import CorruptToolError, MissingToolError, NetworkFailure

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
        ...

    @property
    @abstractmethod
    def download_url(self):
        """The URL where the tool/plugin can be downloaded."""
        ...

    @property
    @abstractmethod
    def file_path(self):
        """The folder on the local filesystem that contains the file_name."""
        ...

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
            raise NetworkFailure(f"downloading {self.full_name}") from e

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

        if not self.exists():
            raise MissingToolError(self.name)

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

    @property
    def plugin_id(self):
        return self.file_name.split(".")[0].split("-")[2]

    @property
    def file_path(self):
        return self.command.tools_path / "linuxdeploy_plugins" / self.plugin_id


class LinuxDeployGtkPlugin(LinuxDeployPluginBase):
    plugin_id = "gtk"
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
    plugin_id = "qt"
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
        super().__init__(command)
        self._file_name = plugin_path.name
        self.local_path = plugin_path.parent
        self._file_path = bundle_path

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
        self.command.shutil.copy(
            self.local_path / self.file_name,
            self.file_path / self.file_name,
        )


class LinuxDeployURLPlugin(LinuxDeployPluginBase):
    full_name = "user-provided linuxdeploy plugin from URL"

    def __init__(self, command, url):
        super().__init__(command)
        self._download_url = url

        url_parts = urlparse(url)
        self._file_name = url_parts.path.split("/")[-1]

        # Build a hash of the download URL; this hash is used to
        # idenfity plugins downloaded from different sources
        self.hash = hashlib.sha256()
        for part in url_parts:
            self.hash.update(part.encode("utf-8"))

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
            plugin.plugin_id: plugin
            for plugin in [LinuxDeployGtkPlugin, LinuxDeployQtPlugin]
        }
