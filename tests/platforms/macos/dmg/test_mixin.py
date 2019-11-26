from briefcase.platforms.macOS.dmg import macOSDmgCreateCommand


def test_bundle_path(first_app_config, tmp_path):
    command = macOSDmgCreateCommand(base_path=tmp_path)
    bundle_path = command.bundle_path(first_app_config)

    assert bundle_path == tmp_path / 'macOS' / 'First App.app'


def test_binary_path(first_app_config, tmp_path):
    command = macOSDmgCreateCommand(base_path=tmp_path)
    binary_path = command.binary_path(first_app_config)

    assert binary_path == tmp_path / 'macOS' / 'First App.app'


def test_distribution_path(first_app_config, tmp_path):
    command = macOSDmgCreateCommand(base_path=tmp_path)
    bundle_path = command.bundle_path(first_app_config)

    assert bundle_path == tmp_path / 'macOS' / 'First App.app'
