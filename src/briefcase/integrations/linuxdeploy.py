from requests import exceptions as requests_exceptions

from briefcase.exceptions import MissingToolError, NetworkFailure


class LinuxDeploy:
    name = 'linuxdeploy'
    full_name = 'linuxdeploy'

    def __init__(self, command):
        self.command = command

    @property
    def appimage_name(self):
        return 'linuxdeploy-{command.host_arch}.AppImage'.format(command=self.command)

    @property
    def linuxdeploy_download_url(self):
        return (
            'https://github.com/linuxdeploy/linuxdeploy/'
            'releases/download/continuous/{self.appimage_name}'.format(self=self)
        )

    @property
    def appimage_path(self):
        return self.command.tools_path / self.appimage_name

    @classmethod
    def verify(cls, command, install=True):
        """
        Verify that LinuxDeploy is available.

        :param command: The command that needs to use linuxdeploy
        :param install: Should the tool be installed if it is not found?
        :returns: A valid LinuxDeploy SDK wrapper. If linuxdeploy is not
            available, and was not installed, raises MissingToolError.
        """
        linuxdeploy = LinuxDeploy(command)

        if not linuxdeploy.exists():
            if install:
                linuxdeploy.install()
            else:
                raise MissingToolError('linuxdeploy')

        return LinuxDeploy(command)

    def exists(self):
        return self.appimage_path.exists()

    @property
    def managed_install(self):
        return True

    def install(self):
        """
        Download and install linuxdeploy.
        """
        try:
            linuxdeploy_appimage_path = self.command.download_url(
                url=self.linuxdeploy_download_url,
                download_path=self.command.tools_path
            )
            self.command.os.chmod(linuxdeploy_appimage_path, 0o755)
            self.elf_header_patch()
        except requests_exceptions.ConnectionError:
            raise NetworkFailure('downloading linuxdeploy AppImage')

    def upgrade(self):
        """
        Upgrade an existing linuxdeploy install.
        """
        if self.exists():
            print("Removing old LinuxDeploy install...")
            self.appimage_path.unlink()

            self.install()
            print("...done.")
        else:
            raise MissingToolError('linuxdeploy')

    def elf_header_patch(self):
        """
        Patch the ELF header of the AppImage to ensure it's always executable.

        This patch is necessary on Linux hosts that use AppImageLauncher.
        AppImages use a modified ELF binary header starting at offset 0x08
        for additional identification. If a system has AppImageLauncher,
        the Linux kernel module `binfmt-misc` will try to load the AppImage
        with AppImageLauncher. As this binary does not exist in the Docker
        container context, we patch the ELF header of linuxdeploy to remove
        the AppImage bits, thus making the system treat it like a regular
        ELF binary.

        Citations:
        - https://github.com/AppImage/AppImageKit/issues/1027#issuecomment-1028232809
        - https://github.com/AppImage/AppImageKit/issues/828
        """

        patch = {
            'offset': 0x08,
            'original': bytes.fromhex('414902'),
            'patch': bytes.fromhex('000000')
        }

        with open(self.appimage_path, 'r+b') as appimage:
            appimage.seek(patch['offset'])
            # Check if the header at the offset is the original value
            if appimage.read(len(patch['original'])) == patch['original']:
                appimage.seek(patch['offset'])
                appimage.write(patch['patch'])
                appimage.flush()
                appimage.seek(0)
                print("Patched ELF header of linuxdeploy AppImage.")
            elif appimage.read(len(patch['original'])) == patch['patch']:
                print("ELF header of linuxdeploy AppImage is already patched.")
            else:
                # We should only get here if the AppImage didn't download correctly.
                # In this case, we can't patch the header, so we'll just warn the user.
                print("AppImage header doesn't match expected value. Unable to patch linuxdeploy.")
