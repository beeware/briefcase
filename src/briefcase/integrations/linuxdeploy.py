from requests import exceptions as requests_exceptions

from briefcase.exceptions import NetworkFailure


def verify_linuxdeploy(command):
    """
    Verify that LinuxDeploy is available.

    :param command: The command that needs to use linuxdeploy
    :returns: The path to the linuxdeploy AppImage.
    """

    linuxdeploy_download_url = (
        'https://github.com/linuxdeploy/linuxdeploy/'
        'releases/download/continuous/linuxdeploy-{command.host_arch}.AppImage'.format(
            command=command
        )
    )

    try:
        print()
        print("Ensure we have the linuxdeploy AppImage...")
        linuxdeploy_appimage_path = command.download_url(
            url=linuxdeploy_download_url,
            download_path=command.dot_briefcase_path / 'tools'
        )
        command.os.chmod(str(linuxdeploy_appimage_path), 0o755)
    except requests_exceptions.ConnectionError:
        raise NetworkFailure('downloading linuxdeploy AppImage')

    return linuxdeploy_appimage_path
