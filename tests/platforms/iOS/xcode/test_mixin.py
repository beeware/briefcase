from briefcase.platforms.iOS.xcode import iOSXcodeCreateCommand


def test_binary_path(first_app_config, tmp_path):
    command = iOSXcodeCreateCommand(base_path=tmp_path)
    binary_path = command.binary_path(first_app_config)

    assert binary_path == tmp_path / 'iOS' / 'First App' / 'build' / 'Debug-iphonesimulator' / 'First App.app'


def test_distribution_path(first_app_config, tmp_path):
    command = iOSXcodeCreateCommand(base_path=tmp_path)
    binary_path = command.binary_path(first_app_config)

    assert binary_path == tmp_path / 'iOS' / 'First App' / 'build' / 'Debug-iphonesimulator' / 'First App.app'
