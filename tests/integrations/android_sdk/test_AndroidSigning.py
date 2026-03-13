from subprocess import CalledProcessError
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.android_sdk import AndroidSigning, AndroidSigningConfig


@pytest.fixture
def signing(mock_tools):
    return AndroidSigning(mock_tools)


def test_keytool_path_non_windows(signing, mock_tools):
    """Keytool points to bin/keytool on non-Windows."""
    mock_tools.host_os = "Linux"
    assert signing._keytool == mock_tools.java.java_home / "bin" / "keytool"


def test_keytool_path_windows(signing, mock_tools):
    """Keytool points to bin/keytool.exe on Windows."""
    mock_tools.host_os = "Windows"
    assert signing._keytool == mock_tools.java.java_home / "bin" / "keytool.exe"


def test_keystore_candidates_none(signing, tmp_path):
    """No candidates when there are no .jks files in the search paths."""
    candidates = signing._keystore_candidates(tmp_path)
    assert candidates == []


def test_keystore_candidates_project_root(signing, tmp_path):
    """Finds .jks files in the project root."""
    ks = tmp_path / "my.jks"
    ks.touch()
    candidates = signing._keystore_candidates(tmp_path)
    assert candidates == [ks]


def test_keystore_candidates_dot_android(signing, tmp_path):
    """Finds .jks files in the .android subfolder of the project root."""
    ks = tmp_path / ".android" / "release.jks"
    ks.parent.mkdir(parents=True, exist_ok=True)
    ks.touch()
    candidates = signing._keystore_candidates(tmp_path)
    assert candidates == [ks]


def test_keystore_candidates_home_android(signing, tmp_path, mock_tools):
    """Finds .jks files in the home .android folder."""
    home_android = tmp_path / "home" / ".android"
    home_android.mkdir(parents=True)
    ks = home_android / "debug.jks"
    ks.touch()
    mock_tools.home_path = tmp_path / "home"
    candidates = signing._keystore_candidates(tmp_path / "app")
    assert candidates == [ks]


def test_keystore_candidates_sorted_within_dir(signing, tmp_path):
    """Candidates within a directory are sorted alphabetically."""
    android_dir = tmp_path / ".android"
    android_dir.mkdir(parents=True)
    (android_dir / "z.jks").touch()
    (android_dir / "a.jks").touch()
    candidates = signing._keystore_candidates(tmp_path)
    assert [p.name for p in candidates] == ["a.jks", "z.jks"]


def test_create_keystore(signing, first_app_config, tmp_path, mock_tools):
    """create_keystore runs keytool and returns a signing config."""
    mock_tools.host_os = "Linux"

    config = signing.create_keystore(
        first_app_config,
        base_path=tmp_path,
        keystore_alias="mykey",
        store_password="storepass",
        key_password="keypass",
    )

    expected_path = tmp_path / ".android" / "com.example.first-app.jks"
    assert config == AndroidSigningConfig(
        keystore_path=expected_path,
        alias="mykey",
        store_password="storepass",
        key_password="keypass",
    )
    assert expected_path.parent.exists()

    mock_tools.subprocess.run.assert_called_once_with(
        [
            mock_tools.java.java_home / "bin" / "keytool",
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
    signing, first_app_config, tmp_path, mock_tools
):
    """When key_password is not provided it defaults to store_password."""
    mock_tools.host_os = "Linux"
    mock_tools.console.text_question = MagicMock(return_value="storepass")

    config = signing.create_keystore(
        first_app_config,
        base_path=tmp_path,
        keystore_alias="mykey",
        store_password="storepass",
    )

    assert config.key_password == "storepass"


def test_create_keystore_prompts_for_alias(
    signing, first_app_config, tmp_path, mock_tools
):
    """When keystore_alias is None the user is prompted."""
    mock_tools.host_os = "Linux"
    mock_tools.console.text_question = MagicMock(return_value="prompted-alias")
    mock_tools.console.text_question = MagicMock(return_value="storepass")

    config = signing.create_keystore(first_app_config, base_path=tmp_path)

    mock_tools.console.text_question.assert_called_once()
    assert config.alias == "prompted-alias"


def test_create_keystore_prompts_for_password(
    signing, first_app_config, tmp_path, mock_tools
):
    """When store_password is None the user is prompted."""
    mock_tools.host_os = "Linux"
    mock_tools.console.text_question = MagicMock(return_value="prompted-pass")

    config = signing.create_keystore(
        first_app_config,
        base_path=tmp_path,
        keystore_alias="mykey",
    )

    mock_tools.console.text_question.assert_called()
    assert config.store_password == "prompted-pass"
    assert config.key_password == "prompted-pass"


def test_create_keystore_keytool_error(signing, first_app_config, tmp_path, mock_tools):
    """A CalledProcessError from keytool is converted to BriefcaseCommandError."""
    mock_tools.host_os = "Linux"
    mock_tools.subprocess.run.side_effect = CalledProcessError(
        returncode=1, cmd=["keytool"]
    )

    with pytest.raises(BriefcaseCommandError, match="Failed to create keystore"):
        signing.create_keystore(
            first_app_config,
            base_path=tmp_path,
            keystore_alias="mykey",
            store_password="storepass",
            key_password="keypass",
        )


def test_select_keystore_identity_provided(signing, first_app_config, tmp_path):
    """When --identity is given as an existing path it is used directly."""
    ks = tmp_path / "release.jks"
    ks.touch()

    config = signing.select_keystore(
        first_app_config,
        base_path=tmp_path,
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
    signing, first_app_config, tmp_path, mock_tools
):
    """key_password defaults to keystore_password when not specified."""
    ks = tmp_path / "release.jks"
    ks.touch()

    config = signing.select_keystore(
        first_app_config,
        base_path=tmp_path,
        identity=str(ks),
        keystore_alias="mykey",
        keystore_password="storepass",
    )

    assert config.key_password == "storepass"


def test_select_keystore_identity_missing_file(signing, first_app_config, tmp_path):
    """A non-existent path raises BriefcaseCommandError."""
    with pytest.raises(BriefcaseCommandError, match="does not exist"):
        signing.select_keystore(
            first_app_config,
            base_path=tmp_path,
            identity=str(tmp_path / "missing.jks"),
        )


def test_select_keystore_identity_prompts_for_alias(
    signing, first_app_config, tmp_path, mock_tools
):
    """When identity is given but keystore_alias is not, the user is prompted."""
    ks = tmp_path / "release.jks"
    ks.touch()
    mock_tools.console.text_question = MagicMock(return_value="prompted-alias")
    mock_tools.console.text_question = MagicMock(return_value="storepass")

    config = signing.select_keystore(
        first_app_config,
        base_path=tmp_path,
        identity=str(ks),
    )

    mock_tools.console.text_question.assert_called_once()
    assert config.alias == "prompted-alias"


def test_select_keystore_identity_prompts_for_password(
    signing, first_app_config, tmp_path, mock_tools
):
    """When identity is given but keystore_password is not, the user is prompted."""
    ks = tmp_path / "release.jks"
    ks.touch()
    mock_tools.console.text_question = MagicMock(return_value="prompted-pass")

    config = signing.select_keystore(
        first_app_config,
        base_path=tmp_path,
        identity=str(ks),
        keystore_alias="mykey",
    )

    mock_tools.console.text_question.assert_called_once()
    assert config.store_password == "prompted-pass"


def test_select_keystore_no_candidates_create_new(
    signing, first_app_config, tmp_path, mock_tools
):
    """With no existing keystores the user is offered only 'create new', and choosing it
    calls create_keystore."""
    mock_tools.host_os = "Linux"
    mock_tools.console.selection_question = MagicMock(return_value="__create_new__")
    signing.create_keystore = MagicMock(
        return_value=AndroidSigningConfig(
            keystore_path=tmp_path / "new.jks",
            alias="mykey",
            store_password="pass",
            key_password="pass",
        )
    )

    config = signing.select_keystore(
        first_app_config,
        base_path=tmp_path,
        keystore_alias="mykey",
        keystore_password="pass",
        key_password="pass",
    )

    # selection_question was called; the only option is "create new"
    call_kwargs = mock_tools.console.selection_question.call_args
    options = call_kwargs.kwargs["options"]
    assert list(options.keys()) == ["__create_new__"]

    signing.create_keystore.assert_called_once_with(
        first_app_config,
        base_path=tmp_path,
        keystore_alias="mykey",
        store_password="pass",
        key_password="pass",
    )
    assert config.keystore_path == tmp_path / "new.jks"


def test_select_keystore_with_candidates_shown(
    signing, first_app_config, tmp_path, mock_tools
):
    """Discovered .jks files appear in the selection alongside 'create new'."""
    ks = tmp_path / ".android" / "app.jks"
    ks.parent.mkdir(parents=True, exist_ok=True)
    ks.touch()

    mock_tools.console.selection_question = MagicMock(return_value=str(ks))
    mock_tools.console.text_question = MagicMock(return_value="mykey")
    mock_tools.console.text_question = MagicMock(return_value="storepass")

    config = signing.select_keystore(first_app_config, base_path=tmp_path)

    call_kwargs = mock_tools.console.selection_question.call_args
    options = call_kwargs.kwargs["options"]
    assert "__create_new__" in options
    assert str(ks) in options

    assert config.keystore_path == ks
    assert config.alias == "mykey"
    assert config.store_password == "storepass"


def test_select_keystore_select_existing_prompts_alias_and_password(
    signing, first_app_config, tmp_path, mock_tools
):
    """Selecting an existing keystore without pre-supplied credentials prompts."""
    ks = tmp_path / ".android" / "app.jks"
    ks.parent.mkdir(parents=True, exist_ok=True)
    ks.touch()

    mock_tools.console.selection_question = MagicMock(return_value=str(ks))
    mock_tools.console.text_question = MagicMock(return_value="myalias")
    mock_tools.console.text_question = MagicMock(return_value="mypassword")

    config = signing.select_keystore(first_app_config, base_path=tmp_path)

    mock_tools.console.text_question.assert_called_once()
    mock_tools.console.text_question.assert_called_once()
    assert config.alias == "myalias"
    assert config.store_password == "mypassword"
    assert config.key_password == "mypassword"
