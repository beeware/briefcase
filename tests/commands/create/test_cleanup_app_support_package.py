import shutil
from unittest import mock

from ...utils import create_file


def test_no_support_path(create_command, myapp, no_support_path_index):
    """If support_path is not listed in briefcase.toml, no cleanup will be performed."""
    create_command.tools.download.file = mock.MagicMock()
    create_command.cleanup_app_support_package(myapp)
    create_command.tools.download.file.assert_not_called()


def test_support_path_does_not_exist(
    create_command,
    myapp,
    app_requirements_path_index,
):
    """If support_path is defined, but the folder doesn't exist, no cleanup is
    needed."""
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)

    create_command.cleanup_app_support_package(myapp)

    # No cleanup was performed.
    create_command.tools.shutil.assert_not_called()


def test_cleanup_support_package(
    create_command,
    myapp,
    support_path,
    app_requirements_path_index,
):
    """If a support package already exists, it can be cleaned up."""

    # Mock an existing support file
    create_file(support_path / "old/trash.txt", "Old support file")

    # Mock shutil so we can confirm that rmtree is called,
    # but we still want the side effect of calling it
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.shutil.rmtree.side_effect = shutil.rmtree

    # Re-install the support package
    create_command.cleanup_app_support_package(myapp)

    # The old support package was deleted
    create_command.tools.shutil.rmtree.assert_called_with(support_path)

    # Confirm that the old support files have been removed
    assert not support_path.exists()
