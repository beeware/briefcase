"""Tests for Android signing coordination in GradlePackageCommand.package_app."""

from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import AndroidSigningConfig

from ....utils import create_file


@pytest.fixture
def first_app_aab(first_app_config):
    first_app_config.packaging_format = "aab"
    return first_app_config


@pytest.fixture
def first_app_debug_apk(first_app_config):
    first_app_config.packaging_format = "debug-apk"
    return first_app_config


def test_package_app_extra_content_signing_skips_keystore_prompt(
    package_command, first_app_aab, tmp_path
):
    """If build_gradle_extra_content has signingConfig, our signing is skipped."""
    first_app_aab.build_gradle_extra_content = """\
android {
    signingConfigs {
        release { storeFile file("my.jks") }
    }
    buildTypes {
        release { signingConfig signingConfigs.release }
    }
}
"""
    package_command.tools.android_sdk.signing.select_keystore = MagicMock()

    def create_bundle(*args, **kwargs):
        create_file(
            tmp_path
            / "base_path"
            / "build"
            / "first-app"
            / "android"
            / "gradle"
            / "app"
            / "build"
            / "outputs"
            / "bundle"
            / "release"
            / "app-release.aab",
            "Android release",
        )

    package_command.tools.subprocess.run.side_effect = create_bundle
    package_command.package_app(first_app_aab)

    # select_keystore was never called
    package_command.tools.android_sdk.signing.select_keystore.assert_not_called()
    # Gradle was invoked without signing -P properties
    call_args = package_command.tools.subprocess.run.call_args[0][0]
    assert not any("-Pandroid.injected.signing" in str(a) for a in call_args)


def test_package_app_extra_content_signing_with_identity_raises(
    package_command, first_app_aab, tmp_path
):
    """Passing --identity alongside build_gradle_extra_content signing raises an
    error."""
    first_app_aab.build_gradle_extra_content = "signingConfig signingConfigs.release"
    keystore = tmp_path / "my.jks"
    keystore.touch()

    with pytest.raises(BriefcaseCommandError, match="Cannot use --identity"):
        package_command.package_app(first_app_aab, identity=str(keystore))


def test_debug_apk_skips_signing(package_command, first_app_debug_apk, tmp_path):
    """Debug-apk format never calls select_keystore, even without --adhoc-sign."""
    package_command.tools.android_sdk.signing.select_keystore = MagicMock()

    def create_bundle(*args, **kwargs):
        create_file(
            tmp_path
            / "base_path"
            / "build"
            / "first-app"
            / "android"
            / "gradle"
            / "app"
            / "build"
            / "outputs"
            / "apk"
            / "debug"
            / "app-debug.apk",
            "Android debug",
        )

    package_command.tools.subprocess.run.side_effect = create_bundle
    package_command.package_app(first_app_debug_apk)

    package_command.tools.android_sdk.signing.select_keystore.assert_not_called()


def test_package_app_calls_select_keystore_for_release(
    package_command, first_app_aab, tmp_path
):
    """package_app calls select_keystore for release formats when not adhoc."""
    signing_config = AndroidSigningConfig(
        keystore_path=tmp_path / "my.jks",
        alias="mykey",
        store_password="storepass",
        key_password="keypass",
    )
    package_command.tools.android_sdk.signing.select_keystore = MagicMock(
        return_value=signing_config
    )

    def create_bundle(*args, **kwargs):
        create_file(
            tmp_path
            / "base_path"
            / "build"
            / "first-app"
            / "android"
            / "gradle"
            / "app"
            / "build"
            / "outputs"
            / "bundle"
            / "release"
            / "app-release.aab",
            "Android release",
        )

    package_command.tools.subprocess.run.side_effect = create_bundle
    package_command.package_app(first_app_aab)

    package_command.tools.android_sdk.signing.select_keystore.assert_called_once_with(
        first_app_aab,
        base_path=package_command.base_path,
        identity=None,
        keystore_alias=None,
        keystore_password=None,
        key_password=None,
    )


def test_package_app_extra_content_without_signingconfig_still_prompts(
    package_command, first_app_aab, tmp_path
):
    """build_gradle_extra_content without 'signingConfig' does not suppress signing."""
    first_app_aab.build_gradle_extra_content = "android { compileSdk 34 }"
    signing_config = AndroidSigningConfig(
        keystore_path=tmp_path / "my.jks",
        alias="mykey",
        store_password="storepass",
        key_password="keypass",
    )
    package_command.tools.android_sdk.signing.select_keystore = MagicMock(
        return_value=signing_config
    )

    def create_bundle(*args, **kwargs):
        create_file(
            tmp_path
            / "base_path"
            / "build"
            / "first-app"
            / "android"
            / "gradle"
            / "app"
            / "build"
            / "outputs"
            / "bundle"
            / "release"
            / "app-release.aab",
            "Android release",
        )

    package_command.tools.subprocess.run.side_effect = create_bundle
    package_command.package_app(first_app_aab)

    package_command.tools.android_sdk.signing.select_keystore.assert_called_once()


def test_package_app_extra_content_signing_adhoc_no_warning(
    package_command, first_app_aab, tmp_path
):
    """When --adhoc-sign is set alongside build_gradle_extra_content signing, no
    migration warning is printed."""
    first_app_aab.build_gradle_extra_content = "signingConfig signingConfigs.release"
    package_command.console.warning = MagicMock()

    def create_bundle(*args, **kwargs):
        create_file(
            tmp_path
            / "base_path"
            / "build"
            / "first-app"
            / "android"
            / "gradle"
            / "app"
            / "build"
            / "outputs"
            / "bundle"
            / "release"
            / "app-release.aab",
            "Android release",
        )

    package_command.tools.subprocess.run.side_effect = create_bundle
    package_command.package_app(first_app_aab, adhoc_sign=True)

    package_command.console.warning.assert_not_called()
