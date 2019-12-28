from briefcase.platforms.macOS.app import macOSAppCreateCommand


def test_binary_path(first_app_config, tmp_path):
    command = macOSAppCreateCommand(base_path=tmp_path)
    binary_path = command.binary_path(first_app_config)

    assert binary_path == tmp_path / 'macOS' / 'First App' / 'First App.app'


def test_distribution_path(first_app_config, tmp_path):
    command = macOSAppCreateCommand(base_path=tmp_path)
    distribution_path = command.distribution_path(first_app_config)

    assert distribution_path == tmp_path / 'macOS' / 'First App' / 'First App.app'
