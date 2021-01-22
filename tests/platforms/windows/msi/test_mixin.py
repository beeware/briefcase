from briefcase.platforms.windows.msi import WindowsMSICreateCommand


def test_binary_path(first_app_config, tmp_path):
    command = WindowsMSICreateCommand(base_path=tmp_path)
    binary_path = command.binary_path(first_app_config)

    assert binary_path == tmp_path / 'windows' / 'First App'


def test_binary_path_with_output_dir(first_app_config, tmp_path):
    output_dir = "output"
    first_app_config.output_dir = output_dir
    command = WindowsMSICreateCommand(base_path=tmp_path)
    binary_path = command.binary_path(first_app_config)

    assert binary_path == tmp_path / output_dir / 'First App'


def test_distribution_path(first_app_config, tmp_path):
    command = WindowsMSICreateCommand(base_path=tmp_path)
    distribution_path = command.distribution_path(first_app_config)

    assert distribution_path == tmp_path / 'windows' / 'First App-0.0.1.msi'


def test_distribution_path_with_output_dir(first_app_config, tmp_path):
    output_dir = "output"
    first_app_config.output_dir = output_dir
    command = WindowsMSICreateCommand(base_path=tmp_path)
    distribution_path = command.distribution_path(first_app_config)

    assert distribution_path == tmp_path / output_dir / 'First App-0.0.1.msi'
