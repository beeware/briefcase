from subprocess import CalledProcessError
from unittest import mock
from zipfile import ZipFile

import pytest

import briefcase.platforms.windows
from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.windows_sdk import WindowsSDK
from briefcase.integrations.wix import WiX
from briefcase.platforms.windows.app import WindowsAppPackageCommand

from ....utils import create_file


@pytest.fixture
def package_command(tmp_path):
    command = WindowsAppPackageCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.host_os = "Windows"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command.tools.wix = WiX(command.tools, wix_home=tmp_path / "wix")
    command.tools.windows_sdk = WindowsSDK(
        tools=command.tools,
        root_path=tmp_path / "windows_sdk",
        version="81.2.1.0",
        arch="groovy",
    )
    return command


@pytest.fixture
def package_command_with_files(package_command, tmp_path):
    # Build the paths for the source and the distribution folders:
    src_path = tmp_path / "base_path/build/first-app/windows/app/src"
    dist_path = tmp_path / "base_path/dist"
    src_path.mkdir(parents=True)
    dist_path.mkdir(parents=True)

    # Mock some typical folders and files in the src folder:
    files = (
        src_path / "First App.exe",
        src_path / "python.exe",
        src_path / "python3.dll",
        src_path / "vcruntime140.dll",
        src_path / "app/first-app/app.py",
        src_path / "app/first-app/resources/__init__.py",
        src_path / "app/first-app-0.0.1.dist-info/top_level.txt",
        src_path / "app_packages/clr.py",
        src_path / "app_packages/toga_winforms/command.py",
    )
    for file in files:
        create_file(file, "")

    return package_command


def test_package_formats(package_command):
    """Packaging formats are as expected."""
    assert package_command.packaging_formats == ["msi", "zip"]
    assert package_command.default_packaging_format == "msi"


def test_verify(package_command, monkeypatch):
    """Verifying on Windows creates a WiX wrapper."""
    # prime Command to _not_ need Windows SDK
    package_command._windows_sdk_needed = False

    mock_wix_verify = mock.MagicMock(wraps=WiX.verify)
    monkeypatch.setattr(
        briefcase.platforms.windows.WiX,
        "verify",
        mock_wix_verify,
    )

    package_command.verify_tools()

    # WiX tool was verified
    mock_wix_verify.assert_called_once_with(tools=package_command.tools)
    assert isinstance(package_command.tools.wix, WiX)


def test_verify_with_signing(package_command, monkeypatch):
    """Verifying on Windows creates WiX and WindowsSDK wrappers when code signing."""
    # prime Command to need Windows SDK
    package_command._windows_sdk_needed = True

    mock_windows_sdk_verify = mock.MagicMock(wraps=WindowsSDK.verify)
    monkeypatch.setattr(
        briefcase.platforms.windows.WindowsSDK,
        "verify",
        mock_windows_sdk_verify,
    )

    mock_wix_verify = mock.MagicMock(wraps=WiX.verify)
    monkeypatch.setattr(
        briefcase.platforms.windows.WiX,
        "verify",
        mock_wix_verify,
    )

    package_command.verify_tools()

    # WiX tool was verified
    mock_wix_verify.assert_called_once_with(tools=package_command.tools)
    assert isinstance(package_command.tools.wix, WiX)
    # WindowsSDK tool was verified
    mock_windows_sdk_verify.assert_called_once_with(tools=package_command.tools)
    assert isinstance(package_command.tools.windows_sdk, WindowsSDK)


@pytest.mark.parametrize(
    "cli_args, signing_options, is_sdk_needed",
    [
        ([], {}, False),
        (["--adhoc-sign"], dict(adhoc_sign=True), False),
        (["--file-digest", "sha2000"], dict(file_digest="sha2000"), False),
        (["-i", "asdf"], dict(identity="asdf"), True),
        (["--identity", "asdf"], dict(identity="asdf"), True),
        (["--identity", "asdf"], dict(identity="asdf"), True),
        (
            [
                "-i",
                "asdf",
                "--file-digest",
                "sha42",
                "--use-local-machine-stores",
                "--cert-store",
                "mystore",
                "--timestamp-url",
                "http://freetimestamps.com",
                "--timestamp-digest",
                "sha56",
            ],
            dict(
                identity="asdf",
                file_digest="sha42",
                use_local_machine=True,
                cert_store="mystore",
                timestamp_url="http://freetimestamps.com",
                timestamp_digest="sha56",
            ),
            True,
        ),
        (
            [
                "-i",
                "asdf",
                "--file-digest",
                "sha42",
                "--cert-store",
                "mystore",
                "--timestamp-url",
                "http://freetimestamps.com",
                "--timestamp-digest",
                "sha56",
            ],
            dict(
                identity="asdf",
                file_digest="sha42",
                cert_store="mystore",
                timestamp_url="http://freetimestamps.com",
                timestamp_digest="sha56",
            ),
            True,
        ),
    ],
)
def test_parse_options(package_command, cli_args, signing_options, is_sdk_needed):
    """Command line arguments are parsed as expected; Windows SDK is required if an
    identity is specified."""
    default_options = dict(
        identity=None,
        file_digest="sha256",
        use_local_machine=False,
        cert_store="My",
        timestamp_url="http://timestamp.digicert.com",
        timestamp_digest="sha256",
        adhoc_sign=False,
        packaging_format="msi",
        update=False,
    )
    expected_options = {**default_options, **signing_options}

    options, overrides = package_command.parse_options(extra=cli_args)

    assert options == expected_options
    assert overrides == {}
    assert package_command._windows_sdk_needed is is_sdk_needed


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(),  # Default behavior (adhoc signing)
        {"adhoc_sign": True},  # Explicit adhoc signing
    ],
)
def test_package_msi(package_command, first_app_config, kwargs, tmp_path):
    """A Windows app can be packaged as an MSI."""

    package_command.package_app(first_app_config, **kwargs)

    assert package_command.tools.subprocess.run.mock_calls == [
        # Collect manifest
        mock.call(
            [
                tmp_path / "wix/bin/heat.exe",
                "dir",
                "src",
                "-nologo",
                "-gg",
                "-sfrag",
                "-sreg",
                "-srd",
                "-scom",
                "-dr",
                "first_app_ROOTDIR",
                "-cg",
                "first_app_COMPONENTS",
                "-var",
                "var.SourceDir",
                "-out",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
        # Compile MSI
        mock.call(
            [
                tmp_path / "wix/bin/candle.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-arch",
                "x64",
                "-dSourceDir=src",
                "first-app.wxs",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
        # Link MSI
        mock.call(
            [
                tmp_path / "wix/bin/light.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-loc",
                "unicode.wxl",
                "-o",
                tmp_path / "base_path/dist/First App-0.0.1.msi",
                "first-app.wixobj",
                "first-app-manifest.wixobj",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
    ]


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(),  # Default behavior (adhoc signing)
        {"adhoc_sign": True},  # Explicit adhoc signing
    ],
)
def test_package_zip(package_command_with_files, first_app_config, kwargs, tmp_path):
    """A Windows app can be packaged as a zip file."""

    first_app_config.packaging_format = "zip"
    package_command_with_files.package_app(first_app_config, **kwargs)

    # No signing was performed
    assert package_command_with_files.tools.subprocess.run.mock_calls == []

    archive_file = tmp_path / "base_path/dist/First App-0.0.1.zip"
    source_folders_and_files = (
        "app/",
        "app/first-app/",
        "app/first-app/resources/",
        "app/first-app-0.0.1.dist-info/",
        "app_packages/",
        "app_packages/toga_winforms/",
        "First App.exe",
        "python.exe",
        "python3.dll",
        "vcruntime140.dll",
        "app/first-app/app.py",
        "app/first-app/resources/__init__.py",
        "app/first-app-0.0.1.dist-info/top_level.txt",
        "app_packages/clr.py",
        "app_packages/toga_winforms/command.py",
    )

    # The zip file exists
    assert archive_file.exists()

    # Check content of zip file
    with ZipFile(archive_file) as archive:
        root = "First App-0.0.1/"
        # All folders and files in zip are from source
        for name in archive.namelist():
            # name.removeprefix(f'{root}') will only work in Python > 3.8
            assert name[len(root) :] in source_folders_and_files
        # All files from source are in zip
        for file in source_folders_and_files:
            assert f"{root}{file}" in archive.namelist()


@pytest.mark.parametrize(
    "use_local_machine, additional_args",
    [(False, []), (True, ["-sm"])],
)
def test_package_msi_with_codesigning(
    package_command,
    first_app_config,
    tmp_path,
    use_local_machine,
    additional_args,
):
    """A Windows app can be packaged as an MSI and code signed."""

    package_command.package_app(
        first_app_config,
        identity="80ee4c3321122916f5637522451993c2a0a4a56a",
        file_digest="sha42",
        use_local_machine=use_local_machine,
        cert_store="mystore",
        timestamp_url="http://freetimestamps.com",
        timestamp_digest="sha56",
    )

    assert package_command.tools.subprocess.run.mock_calls == [
        # Codesign app exe
        mock.call(
            [
                tmp_path
                / "windows_sdk"
                / "bin"
                / "81.2.1.0"
                / "groovy"
                / "signtool.exe",
                "sign",
                "-s",
                "mystore",
                "-sha1",
                "80ee4c3321122916f5637522451993c2a0a4a56a",
                "-fd",
                "sha42",
                "-d",
                "The first simple app \\ demonstration",
                "-du",
                "https://example.com/first-app",
                "-tr",
                "http://freetimestamps.com",
                "-td",
                "sha56",
            ]
            + additional_args
            + [
                tmp_path
                / "base_path"
                / "build"
                / "first-app"
                / "windows"
                / "app"
                / "src"
                / "First App.exe"
            ],
            check=True,
        ),
        # Collect manifest
        mock.call(
            [
                tmp_path / "wix/bin/heat.exe",
                "dir",
                "src",
                "-nologo",
                "-gg",
                "-sfrag",
                "-sreg",
                "-srd",
                "-scom",
                "-dr",
                "first_app_ROOTDIR",
                "-cg",
                "first_app_COMPONENTS",
                "-var",
                "var.SourceDir",
                "-out",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
        # Compile MSI
        mock.call(
            [
                tmp_path / "wix/bin/candle.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-arch",
                "x64",
                "-dSourceDir=src",
                "first-app.wxs",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
        # Link MSI
        mock.call(
            [
                tmp_path / "wix/bin/light.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-loc",
                "unicode.wxl",
                "-o",
                tmp_path / "base_path/dist/First App-0.0.1.msi",
                "first-app.wixobj",
                "first-app-manifest.wixobj",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
        # Codesign app MSI
        mock.call(
            [
                tmp_path
                / "windows_sdk"
                / "bin"
                / "81.2.1.0"
                / "groovy"
                / "signtool.exe",
                "sign",
                "-s",
                "mystore",
                "-sha1",
                "80ee4c3321122916f5637522451993c2a0a4a56a",
                "-fd",
                "sha42",
                "-d",
                "The first simple app \\ demonstration",
                "-du",
                "https://example.com/first-app",
                "-tr",
                "http://freetimestamps.com",
                "-td",
                "sha56",
            ]
            + additional_args
            + [tmp_path / "base_path/dist/First App-0.0.1.msi"],
            check=True,
        ),
    ]


@pytest.mark.parametrize(
    "use_local_machine, additional_args",
    [(False, []), (True, ["-sm"])],
)
def test_package_zip_with_codesigning(
    package_command_with_files,
    first_app_config,
    tmp_path,
    use_local_machine,
    additional_args,
):
    """In a ZIP package, only the binary will be code signed."""

    first_app_config.packaging_format = "zip"

    package_command_with_files.package_app(
        first_app_config,
        identity="80ee4c3321122916f5637522451993c2a0a4a56a",
        file_digest="sha42",
        use_local_machine=use_local_machine,
        cert_store="mystore",
        timestamp_url="http://freetimestamps.com",
        timestamp_digest="sha56",
    )

    assert package_command_with_files.tools.subprocess.run.mock_calls == [
        # Codesign app exe
        mock.call(
            [
                tmp_path
                / "windows_sdk"
                / "bin"
                / "81.2.1.0"
                / "groovy"
                / "signtool.exe",
                "sign",
                "-s",
                "mystore",
                "-sha1",
                "80ee4c3321122916f5637522451993c2a0a4a56a",
                "-fd",
                "sha42",
                "-d",
                "The first simple app \\ demonstration",
                "-du",
                "https://example.com/first-app",
                "-tr",
                "http://freetimestamps.com",
                "-td",
                "sha56",
            ]
            + additional_args
            + [
                tmp_path
                / "base_path"
                / "build"
                / "first-app"
                / "windows"
                / "app"
                / "src"
                / "First App.exe"
            ],
            check=True,
        ),
    ]


def test_package_msi_invalid_identity(package_command, first_app_config):
    """Codesigning fails, along with packaging, if the identity is invalid."""
    with pytest.raises(
        BriefcaseCommandError,
        match="Codesigning identify 'asdf' must be a certificate SHA-1 thumbprint",
    ):
        package_command.package_app(first_app_config, identity="asdf")


def test_package_msi_failed_sign_app(package_command, first_app_config, tmp_path):
    """An error is raised if signtool fails for the app exe."""
    # Mock a failure in the call to signtool.exe
    package_command.tools.subprocess.run.side_effect = [
        CalledProcessError(cmd=["signtool.exe"], returncode=1),
    ]

    with pytest.raises(BriefcaseCommandError, match=r"Unable to sign "):
        package_command.package_app(
            first_app_config,
            identity="80ee4c3321122916f5637522451993c2a0a4a56a",
            file_digest="sha42",
            cert_store="mystore",
            timestamp_url="http://freetimestamps.com",
            timestamp_digest="sha56",
        )

    assert package_command.tools.subprocess.run.mock_calls == [
        # Codesign app exe
        mock.call(
            [
                tmp_path
                / "windows_sdk"
                / "bin"
                / "81.2.1.0"
                / "groovy"
                / "signtool.exe",
                "sign",
                "-s",
                "mystore",
                "-sha1",
                "80ee4c3321122916f5637522451993c2a0a4a56a",
                "-fd",
                "sha42",
                "-d",
                "The first simple app \\ demonstration",
                "-du",
                "https://example.com/first-app",
                "-tr",
                "http://freetimestamps.com",
                "-td",
                "sha56",
                tmp_path
                / "base_path"
                / "build"
                / "first-app"
                / "windows"
                / "app"
                / "src"
                / "First App.exe",
            ],
            check=True,
        )
    ]


def test_package_msi_failed_manifest(package_command, first_app_config, tmp_path):
    """An error is raised if a manifest cannot be built."""
    # Mock a failure in the call to heat.exe
    package_command.tools.subprocess.run.side_effect = [
        CalledProcessError(cmd=["heat.exe"], returncode=1),
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to generate manifest for app first-app.",
    ):
        package_command.package_app(first_app_config)

    assert package_command.tools.subprocess.run.mock_calls == [
        # Collect manifest
        mock.call(
            [
                tmp_path / "wix/bin/heat.exe",
                "dir",
                "src",
                "-nologo",
                "-gg",
                "-sfrag",
                "-sreg",
                "-srd",
                "-scom",
                "-dr",
                "first_app_ROOTDIR",
                "-cg",
                "first_app_COMPONENTS",
                "-var",
                "var.SourceDir",
                "-out",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
    ]


def test_package_msi_failed_compile(package_command, first_app_config, tmp_path):
    """An error is raised if compilation failed."""
    # Mock a failure in the call to candle.exe
    package_command.tools.subprocess.run.side_effect = [
        None,  # heat.exe
        CalledProcessError(cmd=["candle.exe"], returncode=1),
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to compile app first-app.",
    ):
        package_command.package_app(first_app_config)

    assert package_command.tools.subprocess.run.mock_calls == [
        # Collect manifest
        mock.call(
            [
                tmp_path / "wix/bin/heat.exe",
                "dir",
                "src",
                "-nologo",
                "-gg",
                "-sfrag",
                "-sreg",
                "-srd",
                "-scom",
                "-dr",
                "first_app_ROOTDIR",
                "-cg",
                "first_app_COMPONENTS",
                "-var",
                "var.SourceDir",
                "-out",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
        # Compile MSI
        mock.call(
            [
                tmp_path / "wix/bin/candle.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-arch",
                "x64",
                "-dSourceDir=src",
                "first-app.wxs",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
    ]


def test_package_msi_failed_link(package_command, first_app_config, tmp_path):
    """An error is raised if linking fails."""
    # Mock a failure in the call to light.exe
    package_command.tools.subprocess.run.side_effect = [
        None,  # heat.exe
        None,  # candle.exe
        CalledProcessError(cmd=["link.exe"], returncode=1),
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to link app first-app.",
    ):
        package_command.package_app(first_app_config)

    assert package_command.tools.subprocess.run.mock_calls == [
        # Collect manifest
        mock.call(
            [
                tmp_path / "wix/bin/heat.exe",
                "dir",
                "src",
                "-nologo",
                "-gg",
                "-sfrag",
                "-sreg",
                "-srd",
                "-scom",
                "-dr",
                "first_app_ROOTDIR",
                "-cg",
                "first_app_COMPONENTS",
                "-var",
                "var.SourceDir",
                "-out",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
        # Compile MSI
        mock.call(
            [
                tmp_path / "wix/bin/candle.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-arch",
                "x64",
                "-dSourceDir=src",
                "first-app.wxs",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
        # Link MSI
        mock.call(
            [
                tmp_path / "wix/bin/light.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-loc",
                "unicode.wxl",
                "-o",
                tmp_path / "base_path/dist/First App-0.0.1.msi",
                "first-app.wixobj",
                "first-app-manifest.wixobj",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
    ]


def test_package_msi_failed_signing_msi(package_command, first_app_config, tmp_path):
    """An error is raised if signtool fails for the app MSI."""
    # Mock a failure in the call to light.exe
    package_command.tools.subprocess.run.side_effect = [
        None,  # signtool.exe
        None,  # heat.exe
        None,  # candle.exe
        None,  # link.exe
        CalledProcessError(cmd=["signtool.exe"], returncode=1),
    ]

    with pytest.raises(BriefcaseCommandError, match=r"Unable to sign "):
        package_command.package_app(
            first_app_config,
            identity="80ee4c3321122916f5637522451993c2a0a4a56a",
            file_digest="sha42",
            cert_store="mystore",
            timestamp_url="http://freetimestamps.com",
            timestamp_digest="sha56",
        )

    assert package_command.tools.subprocess.run.mock_calls == [
        # Codesign app exe
        mock.call(
            [
                tmp_path
                / "windows_sdk"
                / "bin"
                / "81.2.1.0"
                / "groovy"
                / "signtool.exe",
                "sign",
                "-s",
                "mystore",
                "-sha1",
                "80ee4c3321122916f5637522451993c2a0a4a56a",
                "-fd",
                "sha42",
                "-d",
                "The first simple app \\ demonstration",
                "-du",
                "https://example.com/first-app",
                "-tr",
                "http://freetimestamps.com",
                "-td",
                "sha56",
                tmp_path
                / "base_path"
                / "build"
                / "first-app"
                / "windows"
                / "app"
                / "src"
                / "First App.exe",
            ],
            check=True,
        ),
        # Collect manifest
        mock.call(
            [
                tmp_path / "wix/bin/heat.exe",
                "dir",
                "src",
                "-nologo",
                "-gg",
                "-sfrag",
                "-sreg",
                "-srd",
                "-scom",
                "-dr",
                "first_app_ROOTDIR",
                "-cg",
                "first_app_COMPONENTS",
                "-var",
                "var.SourceDir",
                "-out",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
        # Compile MSI
        mock.call(
            [
                tmp_path / "wix/bin/candle.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-arch",
                "x64",
                "-dSourceDir=src",
                "first-app.wxs",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
        # Link MSI
        mock.call(
            [
                tmp_path / "wix/bin/light.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-loc",
                "unicode.wxl",
                "-o",
                tmp_path / "base_path/dist/First App-0.0.1.msi",
                "first-app.wixobj",
                "first-app-manifest.wixobj",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/app",
        ),
        # Codesign app MSI
        mock.call(
            [
                tmp_path
                / "windows_sdk"
                / "bin"
                / "81.2.1.0"
                / "groovy"
                / "signtool.exe",
                "sign",
                "-s",
                "mystore",
                "-sha1",
                "80ee4c3321122916f5637522451993c2a0a4a56a",
                "-fd",
                "sha42",
                "-d",
                "The first simple app \\ demonstration",
                "-du",
                "https://example.com/first-app",
                "-tr",
                "http://freetimestamps.com",
                "-td",
                "sha56",
                tmp_path / "base_path/dist/First App-0.0.1.msi",
            ],
            check=True,
        ),
    ]
