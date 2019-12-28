from briefcase.platforms.linux.appimage import LinuxAppImageCreateCommand


def test_binary_path(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    # Force the architecture to x86_64 for test purposes.
    command.host_arch = 'x86_64'
    binary_path = command.binary_path(first_app_config)

    assert binary_path == tmp_path / 'linux' / 'First_App-0.0.1-x86_64.AppImage'


def test_distribution_path(first_app_config, tmp_path):
    command = LinuxAppImageCreateCommand(base_path=tmp_path)
    # Force the architecture to x86_64 for test purposes.
    command.host_arch = 'x86_64'
    distribution_path = command.distribution_path(first_app_config)

    assert distribution_path == tmp_path / 'linux' / 'First_App-0.0.1-x86_64.AppImage'
