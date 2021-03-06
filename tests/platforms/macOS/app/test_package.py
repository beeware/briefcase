from unittest import mock

import pytest

from briefcase.platforms.macOS.app import macOSAppPackageCommand


@pytest.fixture
def first_app_with_binaries(first_app_config, tmp_path):
    # Create some libraries that need to be signed.
    app_path = tmp_path / 'macOS' / 'app' / 'First App' / 'First App.app'
    lib_path = app_path / 'Contents' / 'Resources'
    lib_path.mkdir(parents=True)
    with (lib_path / 'first_so.so').open('w') as f:
        f.write('library')
    with (lib_path / 'second_so.so').open('w') as f:
        f.write('library')
    with (lib_path / 'first_dylib.dylib').open('w') as f:
        f.write('library')
    with (lib_path / 'second_dylib.dylib').open('w') as f:
        f.write('library')

    # Make sure there are some files in the bundle that *don't* need to be signed...
    with (app_path / 'Contents' / 'first.other').open('w') as f:
        f.write('other')
    with (app_path / 'Contents' / 'second.other').open('w') as f:
        f.write('other')

    return first_app_config


def test_package_app(first_app_with_binaries, tmp_path):
    "A macOS App can be packaged"

    command = macOSAppPackageCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()
    command.dmgbuild = mock.MagicMock()

    command.select_identity = mock.MagicMock(return_value='Sekrit identity (DEADBEEF)')
    command.packaging_format = 'dmg'

    command.package_app(first_app_with_binaries)

    def sign_call(filepath):
        return mock.call(
            [
                'codesign',
                '--sign', 'Sekrit identity (DEADBEEF)',
                '--entitlements', str(tmp_path / 'macOS' / 'app' / 'First App' / 'Entitlements.plist'),
                '--deep', str(filepath),
                '--force',
                '--options', 'runtime',
            ],
            check=True
        )

    # A request has been made to sign all the so and dylib files, plus the
    # app bundle itself.
    app_path = tmp_path / 'macOS' / 'app' / 'First App' / 'First App.app'
    lib_path = app_path / 'Contents' / 'Resources'
    command.subprocess.run.assert_has_calls(
        [
            sign_call(lib_path / 'first_so.so'),
            sign_call(lib_path / 'second_so.so'),
            sign_call(lib_path / 'first_dylib.dylib'),
            sign_call(lib_path / 'second_dylib.dylib'),
            sign_call(app_path),
        ],
        any_order=True
    )

    # The DMG has been built as expected
    command.dmgbuild.build_dmg.assert_called_with(
        filename=str(tmp_path / 'macOS' / 'First App-0.0.1.dmg'),
        volume_name='First App 0.0.1',
        settings={
            'files': [str(tmp_path / 'macOS' / 'app' / 'First App' / 'First App.app')],
            'symlinks': {'Applications': '/Applications'},
            'icon_locations': {
                'First App.app': (75, 75),
                'Applications': (225, 75),
            },
            'window_rect': ((600, 600), (350, 150)),
            'icon_size': 64,
            'text_size': 12,
        }
    )


def test_package_app_no_sign(first_app_with_binaries, tmp_path):
    "A macOS App can be packaged without signing"

    command = macOSAppPackageCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()
    command.dmgbuild = mock.MagicMock()

    command.select_identity = mock.MagicMock(return_value='Sekrit identity (DEADBEEF)')
    command.packaging_format = 'dmg'

    command.package_app(first_app_with_binaries, sign_app=False)

    # No code signing has been performed.
    assert command.select_identity.call_count == 0
    assert command.subprocess.run.call_count == 0


def test_package_app_adhoc_sign(first_app_with_binaries, tmp_path):
    "A macOS App can be packaged and signed with adhoc identity"

    command = macOSAppPackageCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()
    command.dmgbuild = mock.MagicMock()

    command.select_identity = mock.MagicMock(return_value="Sekrit identity (DEADBEEF)")
    command.packaging_format = 'dmg'

    command.package_app(first_app_with_binaries, adhoc_sign=True)

    # the select_identity method has not been used
    assert command.select_identity.call_count == 0
    # but code signing has been performed with "--sign -"
    assert command.subprocess.run.call_args[0][0][1:3] == ["--sign", "-"]


def test_package_app_no_dmg(first_app_with_binaries, tmp_path):
    "A macOS App can be packaged without building dmg"

    command = macOSAppPackageCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()
    command.dmgbuild = mock.MagicMock()

    command.select_identity = mock.MagicMock(return_value='Sekrit identity (DEADBEEF)')
    command.packaging_format = 'app'

    command.package_app(first_app_with_binaries)

    # No dmg was built.
    assert command.dmgbuild.call_count == 0
