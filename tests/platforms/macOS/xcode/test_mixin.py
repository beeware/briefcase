from briefcase.platforms.macOS.xcode import macOSXcodeCreateCommand


def test_binary_path(first_app_config, tmp_path):
    command = macOSXcodeCreateCommand(base_path=tmp_path)
    binary_path = command.binary_path(first_app_config)

    assert binary_path == tmp_path / 'macOS' / 'Xcode' / 'First App' / 'build' / 'Release' / 'First App.app'


def test_distribution_path_app(first_app_config, tmp_path):
    command = macOSXcodeCreateCommand(base_path=tmp_path)

    distribution_path = command.distribution_path(first_app_config, 'app')

    assert distribution_path == tmp_path / 'macOS' / 'Xcode' / 'First App' / 'build' / 'Release' / 'First App.app'


def test_distribution_path_dmg(first_app_config, tmp_path):
    command = macOSXcodeCreateCommand(base_path=tmp_path)

    distribution_path = command.distribution_path(first_app_config, 'dmg')

    assert distribution_path == tmp_path / 'macOS' / 'First App-0.0.1.dmg'


def test_entitlements_path(first_app_config, tmp_path):
    command = macOSXcodeCreateCommand(base_path=tmp_path)
    entitlements_path = command.entitlements_path(first_app_config)

    assert entitlements_path == tmp_path / 'macOS' / 'Xcode' / 'First App' / 'First App' / 'first-app.entitlements'
