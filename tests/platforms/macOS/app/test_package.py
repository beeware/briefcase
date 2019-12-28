from unittest import mock

from briefcase.platforms.macOS.app import macOSAppPackageCommand


def test_package_app(first_app_config, tmp_path):
    "A macOS App can be packaged"
    # Create some libraries that need to be signed.
    app_path = tmp_path / 'macOS' / 'First App' / 'First App.app'
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

    command = macOSAppPackageCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()

    command.select_identity = mock.MagicMock(return_value='Sekrit identity (DEADBEEF)')

    command.package_app(first_app_config)

    def sign_call(filepath):
        return mock.call(
            [
                'codesign',
                '--sign', 'Sekrit identity (DEADBEEF)',
                '--entitlements', str(tmp_path / 'macOS' / 'First App' / 'Entitlements.plist'),
                '--deep', str(filepath),
                '--force',
                '--options', 'runtime',
            ],
            check=True
        )

    # A request has been made to sign all the so and dylib files, plus the
    # app bundle itself.
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
