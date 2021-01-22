import sys

import pytest

from briefcase.platforms.macOS.dmg import macOSDmgCreateCommand

if sys.platform != 'darwin':
    pytest.skip("requires macOS", allow_module_level=True)


def test_binary_path(first_app_config, tmp_path):
    command = macOSDmgCreateCommand(base_path=tmp_path)
    binary_path = command.binary_path(first_app_config)

    assert binary_path == tmp_path / 'macOS' / 'First App' / 'First App.app'


def test_binary_path_with_output_dir(first_app_config, tmp_path):
    output_dir = "output"
    first_app_config.output_dir = output_dir
    command = macOSDmgCreateCommand(base_path=tmp_path)
    binary_path = command.binary_path(first_app_config)

    assert binary_path == tmp_path / output_dir / 'First App' / 'First App.app'


def test_distribution_path(first_app_config, tmp_path):
    command = macOSDmgCreateCommand(base_path=tmp_path)
    distribution_path = command.distribution_path(first_app_config)

    assert distribution_path == tmp_path / 'macOS' / 'First App-0.0.1.dmg'


def test_distribution_path_with_output_dir(first_app_config, tmp_path):
    output_dir = "output"
    first_app_config.output_dir = output_dir
    command = macOSDmgCreateCommand(base_path=tmp_path)
    distribution_path = command.distribution_path(first_app_config)

    assert distribution_path == tmp_path / output_dir / 'First App-0.0.1.dmg'
