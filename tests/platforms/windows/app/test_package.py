from subprocess import CalledProcessError
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.windows_sdk import WindowsSDK
from briefcase.integrations.wix import WiX
from briefcase.platforms.windows.app import WindowsAppPackageCommand


@pytest.fixture
def package_command(tmp_path):
    command = WindowsAppPackageCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command.tools.wix = WiX(command.tools, wix_home=tmp_path / "wix")
    command.tools.windows_sdk = WindowsSDK(
        tools=command.tools,
        root_path=tmp_path / "windows_sdk",
        version="81.2.1.0",
        arch="groovy",
    )
    return command


def test_package_formats(package_command):
    """Packaging formats are as expected."""
    assert package_command.packaging_formats == ["msi"]
    assert package_command.default_packaging_format == "msi"


def test_verify(package_command):
    """Verifying on Windows creates a WiX wrapper."""
    # prime Command to _not_ need Windows SDK
    package_command._windows_sdk_needed = False

    package_command.verify_tools()

    # No error and an SDK wrapper is created
    assert isinstance(package_command.tools.wix, WiX)


def test_verify_with_signing(package_command):
    """Verifying on Windows creates WiX and WindowsSDK wrappers when code signing."""
    # prime Command to need Windows SDK
    package_command._windows_sdk_needed = True

    package_command.verify_tools()

    # No error and SDK wrappers are created
    assert isinstance(package_command.tools.wix, WiX)
    assert isinstance(package_command.tools.windows_sdk, WindowsSDK)


@pytest.mark.parametrize(
    "cli_args, signing_options, is_sdk_needed",
    [
        ([], {}, False),
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
    """Command line arguments are parsed as expected; Windows SDK is required if an identity is specified."""
    default_options = dict(
        identity=None,
        file_digest="sha256",
        use_local_machine=False,
        cert_store="My",
        timestamp_url="http://timestamp.digicert.com",
        timestamp_digest="sha256",
        adhoc_sign=False,
        packaging_format="msi",
        sign_app=True,
        update=False,
    )
    expected_options = {**default_options, **signing_options}

    options = package_command.parse_options(extra=cli_args)

    assert options == expected_options
    assert package_command._windows_sdk_needed is is_sdk_needed


def test_package_msi(package_command, first_app_config, tmp_path):
    """A Windows app can be packaged as an MSI."""

    package_command.package_app(first_app_config)

    assert package_command.tools.subprocess.run.mock_calls == [
        # Collect manifest
        mock.call(
            [
                tmp_path / "wix" / "bin" / "heat.exe",
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
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
        ),
        # Compile MSI
        mock.call(
            [
                tmp_path / "wix" / "bin" / "candle.exe",
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
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
        ),
        # Link MSI
        mock.call(
            [
                tmp_path / "wix" / "bin" / "light.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-loc",
                "unicode.wxl",
                "-o",
                tmp_path / "base_path" / "dist" / "First App-0.0.1.msi",
                "first-app.wixobj",
                "first-app-manifest.wixobj",
            ],
            check=True,
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
        ),
    ]


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
                tmp_path / "wix" / "bin" / "heat.exe",
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
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
        ),
        # Compile MSI
        mock.call(
            [
                tmp_path / "wix" / "bin" / "candle.exe",
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
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
        ),
        # Link MSI
        mock.call(
            [
                tmp_path / "wix" / "bin" / "light.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-loc",
                "unicode.wxl",
                "-o",
                tmp_path / "base_path" / "dist" / "First App-0.0.1.msi",
                "first-app.wixobj",
                "first-app-manifest.wixobj",
            ],
            check=True,
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
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
            + [tmp_path / "base_path" / "dist" / "First App-0.0.1.msi"],
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
                tmp_path / "wix" / "bin" / "heat.exe",
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
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
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
                tmp_path / "wix" / "bin" / "heat.exe",
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
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
        ),
        # Compile MSI
        mock.call(
            [
                tmp_path / "wix" / "bin" / "candle.exe",
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
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
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
                tmp_path / "wix" / "bin" / "heat.exe",
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
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
        ),
        # Compile MSI
        mock.call(
            [
                tmp_path / "wix" / "bin" / "candle.exe",
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
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
        ),
        # Link MSI
        mock.call(
            [
                tmp_path / "wix" / "bin" / "light.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-loc",
                "unicode.wxl",
                "-o",
                tmp_path / "base_path" / "dist" / "First App-0.0.1.msi",
                "first-app.wixobj",
                "first-app-manifest.wixobj",
            ],
            check=True,
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
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
                tmp_path / "wix" / "bin" / "heat.exe",
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
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
        ),
        # Compile MSI
        mock.call(
            [
                tmp_path / "wix" / "bin" / "candle.exe",
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
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
        ),
        # Link MSI
        mock.call(
            [
                tmp_path / "wix" / "bin" / "light.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-loc",
                "unicode.wxl",
                "-o",
                tmp_path / "base_path" / "dist" / "First App-0.0.1.msi",
                "first-app.wixobj",
                "first-app-manifest.wixobj",
            ],
            check=True,
            cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
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
                tmp_path / "base_path" / "dist" / "First App-0.0.1.msi",
            ],
            check=True,
        ),
    ]
