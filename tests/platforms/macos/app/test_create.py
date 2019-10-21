from briefcase.platforms.macos.app import MacOSAppCreateCommand


def test_binary_path(first_app_config, tmp_path):
    command = MacOSAppCreateCommand()
    binary_path = command.binary_path(first_app_config, tmp_path)

    assert binary_path == tmp_path / 'macos' / 'First App.app'


def test_bundle_path(first_app_config, tmp_path):
    command = MacOSAppCreateCommand()
    bundle_path = command.bundle_path(first_app_config, tmp_path)

    assert bundle_path == tmp_path / 'macos' / 'First App.app'
