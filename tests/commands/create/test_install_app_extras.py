from unittest import mock

from briefcase.config import AppConfig


def test_no_extras(create_command):
    "If the template defines no extra targets, none are installed"
    myapp = AppConfig(
        name='my-app',
        formal_name='My App',
        bundle='com.example',
        version='1.2.3',
        description='This is a simple app',
    )

    # Prime the path index with no targets
    create_command._path_index = {myapp: {}}

    install_image = mock.MagicMock()
    create_command.install_image = install_image

    # Install app extras
    create_command.install_app_extras(myapp)

    # No icons, splash image or document types, so no calls to install images
    install_image.assert_not_called()


def test_icon_target(create_command, tmp_path):
    "If the template defines an icon target, it will be installed"
    myapp = AppConfig(
        name='my-app',
        formal_name='My App',
        bundle='com.example',
        version='1.2.3',
        description='This is a simple app',
        icon='images/icon.png'
    )

    # Prime the path index with 2 icon targets
    create_command._path_index = {
        myapp: {
            'icon': {
                '10': 'path/to/icon-10.png',
                '20': 'path/to/icon-20.png',
            }
        }
    }

    install_image = mock.MagicMock()
    create_command.install_image = install_image

    # Install app extras
    create_command.install_app_extras(myapp)

    # 2 calls to install icons will be made
    install_image.assert_has_calls([
        mock.call(
            'application icon',
            size='10',
            sources='images/icon.png',
            target=tmp_path / 'tester/my-app.bundle/path/to/icon-10.png'
        ),
        mock.call(
            'application icon',
            size='20',
            sources='images/icon.png',
            target=tmp_path / 'tester/my-app.bundle/path/to/icon-20.png'
        ),
    ], any_order=True)


def test_splash_target(create_command, tmp_path):
    "If the template defines an splash target, it will be installed"
    myapp = AppConfig(
        name='my-app',
        formal_name='My App',
        bundle='com.example',
        version='1.2.3',
        description='This is a simple app',
        splash='images/splash.png'
    )

    # Prime the path index with 2 splash targets
    create_command._path_index = {
        myapp: {
            'splash': {
                '10x20': 'path/to/splash-10x20.png',
                '20x30': 'path/to/splash-20x30.png',
            }
        }
    }

    install_image = mock.MagicMock()
    create_command.install_image = install_image

    # Install app extras
    create_command.install_app_extras(myapp)

    # 2 calls to install splash images will be made
    install_image.assert_has_calls([
        mock.call(
            'splash image',
            size='10x20',
            sources='images/splash.png',
            target=tmp_path / 'tester/my-app.bundle/path/to/splash-10x20.png'
        ),
        mock.call(
            'splash image',
            size='20x30',
            sources='images/splash.png',
            target=tmp_path / 'tester/my-app.bundle/path/to/splash-20x30.png'
        ),
    ], any_order=True)


def test_doctype_icon_target(create_command, tmp_path):
    "If the template defines document types, their icons will be installed"
    myapp = AppConfig(
        name='my-app',
        formal_name='My App',
        bundle='com.example',
        version='1.2.3',
        description='This is a simple app',
        document_type={
            'mydoc': {
                'icon': 'images/mydoc-icon.png'
            },
            'other': {
                'icon': {
                    '10': 'images/other-icon-10.png',
                    '20': 'images/other-icon-20.png',
                }
            }
        }
    )

    # Prime the path index with 2 document types;
    # * mydoc, which has a single static image; and
    # * other, which has multiple size targets.
    create_command._path_index = {
        myapp: {
            'document_type_icon': {
                'mydoc': 'path/to/mydoc-icon.png',
                'other': {
                    '10': 'path/to/other-icon-10.png',
                    '20': 'path/to/other-icon-20.png',
                }
            }
        }
    }

    install_image = mock.MagicMock()
    create_command.install_image = install_image

    # Install app extras
    create_command.install_app_extras(myapp)

    # 2 calls to install doctype icon images will be made
    install_image.assert_has_calls([
        mock.call(
            'icon for .mydoc documents',
            size=None,
            sources='images/mydoc-icon.png',
            target=tmp_path / 'tester/my-app.bundle/path/to/mydoc-icon.png'
        ),
        mock.call(
            'icon for .other documents',
            size='10',
            sources={
                '10': 'images/other-icon-10.png',
                '20': 'images/other-icon-20.png',
            },
            target=tmp_path / 'tester/my-app.bundle/path/to/other-icon-10.png'
        ),
        mock.call(
            'icon for .other documents',
            size='20',
            sources={
                '10': 'images/other-icon-10.png',
                '20': 'images/other-icon-20.png',
            },
            target=tmp_path / 'tester/my-app.bundle/path/to/other-icon-20.png'
        ),
    ], any_order=True)
