import sys
from unittest import mock

import pytest

from briefcase.platforms.macOS.xcode import macOSXcodeCreateCommand

from ....utils import create_file


@pytest.fixture
def create_command(dummy_console, mock_other_venv, tmp_path):
    command = macOSXcodeCreateCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    command.generate_template = mock.MagicMock()
    command.verify_not_on_icloud = mock.MagicMock()
    command.create_app_environment = mock.MagicMock(return_value=mock_other_venv)
    command.tools.sys = mock.MagicMock(spec_set=sys)
    command.tools.sys.version_info = (3, "X", 0)

    return command


@pytest.mark.parametrize("reinstall", [True, False])
def test_install_managed_python_env(
    create_command,
    mock_venv,
    first_app_generated,
    reinstall,
    tmp_path,
):
    """A managed python environment will be copied into the final app."""
    resource_path = create_command.bundle_path(first_app_generated) / "support/Python"

    # Create some mock content in the virtual environment
    create_file(tmp_path / "mock_venvs/mock-venv/base.txt", "Top level file")
    create_file(tmp_path / "mock_venvs/mock-venv/lib/libpython.so", "Python lib")
    create_file(tmp_path / "mock_venvs/mock-venv/lib/site-packages/test.py", "Stdlib")

    if reinstall:
        # Create an existing symlink
        resource_path.symlink_to(tmp_path / "mock_venvs/mock-venv")

    # Install the managed Python environment
    create_command.install_managed_python_env(first_app_generated, mock_venv)

    # A symlink to the managed install was created
    assert resource_path.is_symlink()
    assert resource_path.resolve() == tmp_path / "mock_venvs/mock-venv"

    # The managed environment was copied to the final app.
    # Deep directory structure is preserved.
    assert (resource_path / "base.txt").resolve().exists()
    assert (resource_path / "lib/libpython.so").resolve().exists()
    assert (resource_path / "lib/site-packages/test.py").resolve().exists()
