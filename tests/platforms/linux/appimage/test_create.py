import sys

from briefcase.platforms.linux.appimage import LinuxAppImageCreateCommand


def test_support_package_url(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(base_path=tmp_path)

    # Set some properties of the host system for test purposes.
    command.host_arch = 'wonky'
    command.platform = 'tester'

    assert command.support_package_url_query == [
        ('platform', 'tester'),
        ('version', '3.{minor}'.format(minor=sys.version_info.minor)),
        ('arch', 'wonky'),
    ]
