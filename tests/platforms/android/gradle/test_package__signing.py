"""Tests for Android keystore signing: select_keystore and create_keystore."""

from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.java import JDK
from briefcase.platforms.android.gradle import AndroidSigningConfig

from ....utils import create_file


@pytest.fixture
def first_app_aab(first_app_config):
    first_app_config.packaging_format = "aab"
    return first_app_config


@pytest.fixture
def package_command_with_java(package_command, tmp_path):
    """Extend the base package_command fixture with a mocked JDK."""
    java_mock = MagicMock(spec=JDK)
    java_mock.java_home = tmp_path / "java"
    package_command.tools.java = java_mock
    return package_command


def test_keytool_path_non_windows(package_command_with_java, tmp_path):
    """Keytool points to bin/keytool on non-Windows."""
    package_command_with_java.tools.host_os = "Linux"
    assert package_command_with_java._keytool == tmp_path / "java" / "bin" / "keytool"


def test_keytool_path_windows(package_command_with_java, tmp_path):
    """Keytool points to bin/keytool.exe on Windows."""
    package_command_with_java.tools.host_os = "Windows"
    assert (
        package_command_with_java._keytool == tmp_path / "java" / "bin" / "keytool.exe"
    )


# ---------------------------------------------------------------------------
# _keystore_candidates
# ---------------------------------------------------------------------------


def test_keystore_candidates_none(package_command, tmp_path):
    """No candidates when there are no .jks files in the search paths."""
    candidates = package_command._keystore_candidates()
    assert candidates == []


def test_keystore_candidates_project_root(package_command, tmp_path):
    """Finds .jks files in the project root."""
    ks = tmp_path / "base_path" / "my.jks"
    ks.parent.mkdir(parents=True, exist_ok=True)
    ks.touch()
    candidates = package_command._keystore_candidates()
    assert candidates == [ks]


def test_keystore_candidates_dot_android(package_command, tmp_path):
    """Finds .jks files in the .android subfolder of the project root."""
    ks = tmp_path / "base_path" / ".android" / "release.jks"
    ks.parent.mkdir(parents=True, exist_ok=True)
    ks.touch()
    candidates = package_command._keystore_candidates()
    assert candidates == [ks]


def test_keystore_candidates_home_android(package_command, tmp_path, monkeypatch):
    """Finds .jks files in ~/.android."""
    home_android = tmp_path / "home" / ".android"
    home_android.mkdir(parents=True)
    ks = home_android / "debug.jks"
    ks.touch()
    package_command.tools.home_path = tmp_path / "home"
    candidates = package_command._keystore_candidates()
    assert candidates == [ks]


def test_keystore_candidates_sorted_within_dir(package_command, tmp_path):
    """Candidates within a directory are sorted alphabetically."""
    android_dir = tmp_path / "base_path" / ".android"
    android_dir.mkdir(parents=True)
    (android_dir / "z.jks").touch()
    (android_dir / "a.jks").touch()
    candidates = package_command._keystore_candidates()
    assert [p.name for p in candidates] == ["a.jks", "z.jks"]


def test_create_keystore(package_command_with_java, first_app_config, tmp_path):
    """create_keystore runs keytool and returns a signing config."""
    package_command_with_java.tools.host_os = "Linux"

    config = package_command_with_java.create_keystore(
        first_app_config,
        keystore_alias="mykey",
        store_password="storepass",
        key_password="keypass",
    )

    expected_path = tmp_path / "base_path" / ".android" / "com.example.first-app.jks"
    assert config == AndroidSigningConfig(
        keystore_path=expected_path,
        alias="mykey",
        store_password="storepass",
        key_password="keypass",
    )
    assert expected_path.parent.exists()

    package_command_with_java.tools.subprocess.run.assert_called_once_with(
        [
            tmp_path / "java" / "bin" / "keytool",
            "-genkeypair",
            "-v",
            "-keystore",
            str(expected_path),
            "-alias",
            "mykey",
            "-keyalg",
            "RSA",
            "-keysize",
            "2048",
            "-validity",
            "10000",
            "-storepass",
            "storepass",
            "-keypass",
            "keypass",
            "-dname",
            "CN=First App, OU=Unknown, O=Unknown, L=Unknown, ST=Unknown, C=Unknown",
        ],
        check=True,
    )


def test_create_keystore_key_password_defaults_to_store_password(
    package_command_with_java, first_app_config, tmp_path
):
    """When key_password is not provided it defaults to store_password."""
    package_command_with_java.tools.host_os = "Linux"
    package_command_with_java.console.password_question = MagicMock(
        return_value="storepass"
    )

    config = package_command_with_java.create_keystore(
        first_app_config,
        keystore_alias="mykey",
        store_password="storepass",
    )

    assert config.key_password == "storepass"


def test_create_keystore_prompts_for_alias(
    package_command_with_java, first_app_config, tmp_path
):
    """When keystore_alias is None the user is prompted."""
    package_command_with_java.tools.host_os = "Linux"
    # Simulate console returning a value for text_question
    package_command_with_java.console.text_question = MagicMock(
        return_value="prompted-alias"
    )
    package_command_with_java.console.password_question = MagicMock(
        return_value="storepass"
    )

    config = package_command_with_java.create_keystore(first_app_config)

    package_command_with_java.console.text_question.assert_called_once()
    assert config.alias == "prompted-alias"


def test_create_keystore_prompts_for_password(
    package_command_with_java, first_app_config, tmp_path
):
    """When store_password is None the user is prompted."""
    package_command_with_java.tools.host_os = "Linux"
    package_command_with_java.console.password_question = MagicMock(
        return_value="prompted-pass"
    )

    config = package_command_with_java.create_keystore(
        first_app_config,
        keystore_alias="mykey",
    )

    package_command_with_java.console.password_question.assert_called()
    assert config.store_password == "prompted-pass"
    assert config.key_password == "prompted-pass"


def test_create_keystore_keytool_error(
    package_command_with_java, first_app_config, tmp_path
):
    """A CalledProcessError from keytool is converted to BriefcaseCommandError."""
    package_command_with_java.tools.host_os = "Linux"
    package_command_with_java.tools.subprocess.run.side_effect = CalledProcessError(
        returncode=1, cmd=["keytool"]
    )

    with pytest.raises(BriefcaseCommandError, match="Failed to create keystore"):
        package_command_with_java.create_keystore(
            first_app_config,
            keystore_alias="mykey",
            store_password="storepass",
            key_password="keypass",
        )


def test_select_keystore_identity_provided(package_command, first_app_config, tmp_path):
    """When --identity is given as an existing path it is used directly."""
    ks = tmp_path / "release.jks"
    ks.touch()

    config = package_command.select_keystore(
        first_app_config,
        identity=str(ks),
        keystore_alias="mykey",
        keystore_password="storepass",
        key_password="keypass",
    )

    assert config == AndroidSigningConfig(
        keystore_path=ks,
        alias="mykey",
        store_password="storepass",
        key_password="keypass",
    )


def test_select_keystore_identity_key_password_defaults(
    package_command, first_app_config, tmp_path
):
    """key_password defaults to keystore_password when not specified."""
    ks = tmp_path / "release.jks"
    ks.touch()

    config = package_command.select_keystore(
        first_app_config,
        identity=str(ks),
        keystore_alias="mykey",
        keystore_password="storepass",
    )

    assert config.key_password == "storepass"


def test_select_keystore_identity_missing_file(
    package_command, first_app_config, tmp_path
):
    """A non-existent path raises BriefcaseCommandError."""
    with pytest.raises(BriefcaseCommandError, match="does not exist"):
        package_command.select_keystore(
            first_app_config,
            identity=str(tmp_path / "missing.jks"),
        )


def test_select_keystore_identity_prompts_for_alias(
    package_command, first_app_config, tmp_path
):
    """When identity is given but keystore_alias is not, the user is prompted."""
    ks = tmp_path / "release.jks"
    ks.touch()
    package_command.console.text_question = MagicMock(return_value="prompted-alias")
    package_command.console.password_question = MagicMock(return_value="storepass")

    config = package_command.select_keystore(
        first_app_config,
        identity=str(ks),
    )

    package_command.console.text_question.assert_called_once()
    assert config.alias == "prompted-alias"


def test_select_keystore_identity_prompts_for_password(
    package_command, first_app_config, tmp_path
):
    """When identity is given but keystore_password is not, the user is prompted."""
    ks = tmp_path / "release.jks"
    ks.touch()
    package_command.console.password_question = MagicMock(return_value="prompted-pass")

    config = package_command.select_keystore(
        first_app_config,
        identity=str(ks),
        keystore_alias="mykey",
    )

    package_command.console.password_question.assert_called_once()
    assert config.store_password == "prompted-pass"


def test_select_keystore_no_candidates_create_new(
    package_command_with_java, first_app_config, tmp_path
):
    """With no existing keystores the user is offered only 'create new', and choosing it
    calls create_keystore."""
    package_command_with_java.tools.host_os = "Linux"
    package_command_with_java.console.selection_question = MagicMock(
        return_value="__create_new__"
    )
    package_command_with_java.create_keystore = MagicMock(
        return_value=AndroidSigningConfig(
            keystore_path=tmp_path / "new.jks",
            alias="mykey",
            store_password="pass",
            key_password="pass",
        )
    )

    config = package_command_with_java.select_keystore(
        first_app_config,
        keystore_alias="mykey",
        keystore_password="pass",
        key_password="pass",
    )

    # selection_question was called; the only option is "create new"
    call_kwargs = package_command_with_java.console.selection_question.call_args
    options = call_kwargs.kwargs["options"]
    assert list(options.keys()) == ["__create_new__"]

    package_command_with_java.create_keystore.assert_called_once_with(
        first_app_config,
        keystore_alias="mykey",
        store_password="pass",
        key_password="pass",
    )
    assert config.keystore_path == tmp_path / "new.jks"


def test_select_keystore_with_candidates_shown(
    package_command, first_app_config, tmp_path
):
    """Discovered .jks files appear in the selection alongside 'create new'."""
    ks = tmp_path / "base_path" / ".android" / "app.jks"
    ks.parent.mkdir(parents=True, exist_ok=True)
    ks.touch()

    package_command.console.selection_question = MagicMock(return_value=str(ks))
    package_command.console.text_question = MagicMock(return_value="mykey")
    package_command.console.password_question = MagicMock(return_value="storepass")

    config = package_command.select_keystore(first_app_config)

    call_kwargs = package_command.console.selection_question.call_args
    options = call_kwargs.kwargs["options"]
    assert "__create_new__" in options
    assert str(ks) in options

    assert config.keystore_path == ks
    assert config.alias == "mykey"
    assert config.store_password == "storepass"


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
    package_command.select_keystore = MagicMock()

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
    package_command.select_keystore.assert_not_called()
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


def test_select_keystore_select_existing_prompts_alias_and_password(
    package_command, first_app_config, tmp_path
):
    """Selecting an existing keystore without pre-supplied credentials prompts."""
    ks = tmp_path / "base_path" / ".android" / "app.jks"
    ks.parent.mkdir(parents=True, exist_ok=True)
    ks.touch()

    package_command.console.selection_question = MagicMock(return_value=str(ks))
    package_command.console.text_question = MagicMock(return_value="myalias")
    package_command.console.password_question = MagicMock(return_value="mypassword")

    config = package_command.select_keystore(first_app_config)

    package_command.console.text_question.assert_called_once()
    package_command.console.password_question.assert_called_once()
    assert config.alias == "myalias"
    assert config.store_password == "mypassword"
    assert config.key_password == "mypassword"


@pytest.fixture
def first_app_debug_apk(first_app_config):
    first_app_config.packaging_format = "debug-apk"
    return first_app_config


def test_debug_apk_skips_signing(package_command, first_app_debug_apk, tmp_path):
    """Debug-apk format never calls select_keystore, even without --adhoc-sign."""
    package_command.select_keystore = MagicMock()

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

    package_command.select_keystore.assert_not_called()


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
    package_command.select_keystore = MagicMock(return_value=signing_config)

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

    package_command.select_keystore.assert_called_once_with(
        first_app_aab,
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
    package_command.select_keystore = MagicMock(return_value=signing_config)

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

    package_command.select_keystore.assert_called_once()


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
