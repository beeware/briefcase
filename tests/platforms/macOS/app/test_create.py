import zipfile
from unittest import mock

from briefcase.platforms.macOS.app import macOSAppCreateCommand


def test_install_app_support_package(first_app_config, tmp_path):
    "A support package can be downloaded and unpacked where it is needed"
    # Write a temporary support zip file which includes the Python lib
    support_file = tmp_path / 'out.zip'
    with zipfile.ZipFile(str(support_file), 'w') as support_zip:
        support_zip.writestr('internal/file.txt', data='hello world')
        support_zip.writestr('Python/Resources/lib/module.py', data='code')

    # create app paths
    app_path = tmp_path / 'macOS' / 'app' / 'First App' / 'First App.app'
    lib_path = app_path / 'Contents' / 'Resources'
    support_path = lib_path / 'Python' / 'Support'
    support_path.mkdir(parents=True)

    create_command = macOSAppCreateCommand(base_path=tmp_path)

    # Modify download_url to return the temp zipfile
    create_command.download_url = mock.MagicMock(return_value=support_file)

    # Mock support package path
    create_command.support_path = mock.MagicMock(return_value=support_path)

    # Install the support package
    create_command.install_app_support_package(first_app_config)

    # Confirm that only the lib was kept
    assert (support_path / 'Python' / 'Resources' / 'lib').exists()
    assert (support_path / 'Python' / 'Resources' / 'lib' / 'module.py').exists()
    assert not (support_path / 'internal').exists()
