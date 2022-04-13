import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS.app import macOSAppPackageCommand


@pytest.fixture
def first_app_with_binaries(first_app_config, tmp_path):
    # Create some libraries that need to be signed.
    app_path = tmp_path / 'macOS' / 'app' / 'First App' / 'First App.app'
    lib_path = app_path / 'Contents' / 'Resources'
    for lib in [
        'first_so.so',
        Path('subfolder') / 'second_so.so',
        'first_dylib.dylib',
        Path('subfolder') / 'second_dylib.dylib',
        'other_binary',
    ]:
        (lib_path / lib).parent.mkdir(parents=True, exist_ok=True)
        with (lib_path / lib).open('wb') as f:
            f.write(b'\xCA\xFE\xBA\xBEBinary content here')

    # Mach-O file that is executable, with an odd extension
    with (lib_path / 'special.binary').open('wb') as f:
        f.write(b'\xCA\xFE\xBA\xBEBinary content here')
    os.chmod(lib_path / 'special.binary', 0o755)

    # An embedded app
    (lib_path / 'Extras.app' / 'Contents' / 'MacOS').mkdir(parents=True, exist_ok=True)
    with (lib_path / 'Extras.app' / 'Contents' / 'MacOS' / 'Extras').open('wb') as f:
        f.write(b'\xCA\xFE\xBA\xBEBinary content here')

    # An embedded framework
    (lib_path / 'Extras.framework' / 'Resources').mkdir(parents=True, exist_ok=True)
    with (lib_path / 'Extras.framework' / 'Resources' / 'extras.dylib').open('wb') as f:
        f.write(b'\xCA\xFE\xBA\xBEBinary content here')

    # Make sure there are some files in the bundle that *don't* need to be signed...
    with (app_path / 'Contents' / 'first.other').open('w') as f:
        f.write('other')
    with (app_path / 'Contents' / 'second.other').open('w') as f:
        f.write('other')

    # A file that has a Mach-O header, but isn't executable
    with (app_path / 'Contents' / 'unknown.binary').open('wb') as f:
        f.write(b'\xCA\xFE\xBA\xBEother')

    return first_app_config


def sign_call(tmp_path, filepath, entitlements=True, deep=False):
    args = [
            'codesign',
            os.fsdecode(filepath),
            '--sign', 'Sekrit identity (DEADBEEF)',
            '--force',
    ]
    if entitlements:
        args.extend([
            '--entitlements',
            os.fsdecode(tmp_path / 'macOS' / 'app' / 'First App' / 'Entitlements.plist'),
        ])
    args.extend([
        '--options', 'runtime',
    ])
    if deep:
        args.append('--deep')

    return mock.call(args, stderr=subprocess.PIPE, check=True)


@pytest.mark.skipif(sys.platform != 'darwin', reason="macOS packaging tests only required on macOS")
def test_package_app(first_app_with_binaries, tmp_path):
    "A macOS App can be packaged"

    command = macOSAppPackageCommand(base_path=tmp_path)

    # Mock the return values of codesign.
    # All files are signed without incident, except for
    # first_so.so, which requires a deep sign, and
    # special.binary, which doesn't need a signature.
    # FIXME: The stderr content has been manufactured to trigger
    # the error handling in the PR, rather than coming from
    # observed content. It would be good to replace this with "real"
    # output if we can reproduce it.
    def mock_codesign_subprocess(args, **kwargs):
        if args[0] == 'codesign':
            if args[1].endswith('/first_so.so'):
                if '--deep' not in args:
                    raise subprocess.CalledProcessError(
                        returncode=1,
                        cmd=args,
                        stderr='File was not signed at all.'.encode('utf-8')
                    )
            elif args[1].endswith('/special.binary'):
                raise subprocess.CalledProcessError(
                    returncode=1,
                    cmd=args,
                    stderr='File has unsupported format for signature.'.encode('utf-8')
                )

    command.subprocess = mock.MagicMock()
    command.subprocess.run.side_effect = mock_codesign_subprocess

    command.dmgbuild = mock.MagicMock()

    command.select_identity = mock.MagicMock(return_value='Sekrit identity (DEADBEEF)')
    command.packaging_format = 'dmg'

    command.package_app(first_app_with_binaries)

    # A request has been made to sign all the so and dylib files, plus the
    # app bundle itself.
    app_path = tmp_path / 'macOS' / 'app' / 'First App' / 'First App.app'
    lib_path = app_path / 'Contents' / 'Resources'
    dmg_path = tmp_path / 'macOS' / 'First App-0.0.1.dmg'
    command.subprocess.run.assert_has_calls(
        [
            sign_call(tmp_path, lib_path / 'subfolder' / 'second_so.so'),
            sign_call(tmp_path, lib_path / 'subfolder' / 'second_dylib.dylib'),
            sign_call(tmp_path, lib_path / 'special.binary'),
            sign_call(tmp_path, lib_path / 'other_binary'),
            sign_call(tmp_path, lib_path / 'first_so.so'),
            sign_call(tmp_path, lib_path / 'first_so.so', deep=True),
            sign_call(tmp_path, lib_path / 'first_dylib.dylib'),
            sign_call(tmp_path, lib_path / 'Extras.framework' / 'Resources' / 'extras.dylib'),
            sign_call(tmp_path, lib_path / 'Extras.framework'),
            sign_call(tmp_path, lib_path / 'Extras.app' / 'Contents' / 'MacOS' / 'Extras'),
            sign_call(tmp_path, lib_path / 'Extras.app'),
            sign_call(tmp_path, app_path),
            sign_call(tmp_path, dmg_path, entitlements=False),
        ],
        any_order=False,
    )

    # The DMG has been built as expected
    command.dmgbuild.build_dmg.assert_called_with(
        filename=os.fsdecode(tmp_path / 'macOS' / 'First App-0.0.1.dmg'),
        volume_name='First App 0.0.1',
        settings={
            'files': [os.fsdecode(tmp_path / 'macOS' / 'app' / 'First App' / 'First App.app')],
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


@pytest.mark.skipif(sys.platform != 'darwin', reason="macOS packaging tests only required on macOS")
def test_package_app_sign_failure(first_app_with_binaries, tmp_path):
    "If the signing process can't be completed, an error is raised"

    command = macOSAppPackageCommand(base_path=tmp_path)

    # Mock the return values of codesign.
    # All files are signed without incident, except for
    # special.binary, which raises an unknown error
    def mock_codesign_subprocess(args, **kwargs):
        if args[0] == 'codesign':
            if args[1].endswith('/special.binary'):
                raise subprocess.CalledProcessError(
                    returncode=1,
                    cmd=args,
                    stderr='Unknown error.'.encode('utf-8')
                )

    command.subprocess = mock.MagicMock()
    command.subprocess.run.side_effect = mock_codesign_subprocess

    command.dmgbuild = mock.MagicMock()

    command.select_identity = mock.MagicMock(return_value='Sekrit identity (DEADBEEF)')
    command.packaging_format = 'dmg'

    with pytest.raises(BriefcaseCommandError, match=r'Unable to code sign'):
        command.package_app(first_app_with_binaries)

    # A request has been made to sign some of the so and dylib files
    app_path = tmp_path / 'macOS' / 'app' / 'First App' / 'First App.app'
    lib_path = app_path / 'Contents' / 'Resources'
    command.subprocess.run.assert_has_calls(
        [
            sign_call(tmp_path, lib_path / 'subfolder' / 'second_so.so'),
            sign_call(tmp_path, lib_path / 'subfolder' / 'second_dylib.dylib'),
            sign_call(tmp_path, lib_path / 'special.binary'),
        ],
        any_order=False,
    )

    # dmgbuild has not been called
    command.dmgbuild.assert_not_called()


@pytest.mark.skipif(sys.platform != 'darwin', reason="macOS packaging tests only required on macOS")
def test_package_app_deep_sign_faliure(first_app_with_binaries, tmp_path):
    "A macOS App can be packaged"

    command = macOSAppPackageCommand(base_path=tmp_path)

    # Mock the return values of codesign.
    # Deep signing on first_so.so raises a unknown error.
    def mock_codesign_subprocess(args, **kwargs):
        if args[0] == 'codesign':
            if args[1].endswith('/first_so.so'):
                if '--deep' not in args:
                    raise subprocess.CalledProcessError(
                        returncode=1,
                        cmd=args,
                        stderr='File was not signed at all.'.encode('utf-8')
                    )
                else:
                    raise subprocess.CalledProcessError(
                        returncode=1,
                        cmd=args,
                        stderr='Unknown error.'.encode('utf-8')
                    )

    command.subprocess = mock.MagicMock()
    command.subprocess.run.side_effect = mock_codesign_subprocess

    command.dmgbuild = mock.MagicMock()

    command.select_identity = mock.MagicMock(return_value='Sekrit identity (DEADBEEF)')
    command.packaging_format = 'dmg'

    with pytest.raises(BriefcaseCommandError, match=r'Unable to deep code sign'):
        command.package_app(first_app_with_binaries)

    # A request has been made to sign some of the so and dylib files
    app_path = tmp_path / 'macOS' / 'app' / 'First App' / 'First App.app'
    lib_path = app_path / 'Contents' / 'Resources'
    command.subprocess.run.assert_has_calls(
        [
            sign_call(tmp_path, lib_path / 'subfolder' / 'second_so.so'),
            sign_call(tmp_path, lib_path / 'subfolder' / 'second_dylib.dylib'),
            sign_call(tmp_path, lib_path / 'special.binary'),
            sign_call(tmp_path, lib_path / 'other_binary'),
            sign_call(tmp_path, lib_path / 'first_so.so'),
            sign_call(tmp_path, lib_path / 'first_so.so', deep=True),
        ],
        any_order=False,
    )

    # dmgbuild has not been called
    command.dmgbuild.assert_not_called()


@pytest.mark.skipif(sys.platform != 'darwin', reason="macOS packaging tests only required on macOS")
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


@pytest.mark.skipif(sys.platform != 'darwin', reason="macOS packaging tests only required on macOS")
def test_package_app_adhoc_sign(first_app_with_binaries, tmp_path):
    "A macOS App can be packaged and signed with adhoc identity"

    command = macOSAppPackageCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()
    command.dmgbuild = mock.MagicMock()

    command.select_identity = mock.MagicMock()
    command.packaging_format = 'dmg'

    command.package_app(first_app_with_binaries, adhoc_sign=True)

    # the select_identity method has not been used
    assert command.select_identity.call_count == 0
    # but code signing has been performed with "--sign -"
    assert command.subprocess.run.call_args[0][0][2:4] == ["--sign", "-"]
    assert '--options' not in command.subprocess.run.call_args[0][0]


@pytest.mark.skipif(sys.platform != 'darwin', reason="macOS packaging tests only required on macOS")
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
