import sys

import pytest

from briefcase.console import Console, Log
from briefcase.platforms.windows.app import WindowsAppCreateCommand


@pytest.mark.parametrize(
    "version, version_triple",
    [
        ("1", "1.0.0"),
        ("1.2", "1.2.0"),
        ("1.2.3", "1.2.3"),
        ("1.2.3.4", "1.2.3"),
        ("1.2.3a4", "1.2.3"),
        ("1.2.3b5", "1.2.3"),
        ("1.2.3rc6", "1.2.3"),
        ("1.2.3.dev7", "1.2.3"),
        ("1.2.3.post8", "1.2.3"),
    ],
)
def test_version_triple(first_app_config, tmp_path, version, version_triple):
    command = WindowsAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    first_app_config.version = version
    context = command.output_format_template_context(first_app_config)

    assert context["version_triple"] == version_triple


def test_explicit_version_triple(first_app_config, tmp_path):
    command = WindowsAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    first_app_config.version = "1.2.3a1"
    first_app_config.version_triple = "2.3.4"

    context = command.output_format_template_context(first_app_config)

    # Explicit version triple is used.
    assert context["version_triple"] == "2.3.4"


def test_guid(first_app_config, tmp_path):
    """A predictable GUID will be generated from the bundle."""
    command = WindowsAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    context = command.output_format_template_context(first_app_config)

    assert context["guid"] == "d666a4f1-c7b7-52cc-888a-3a35a7cc97e5"


def test_explicit_guid(first_app_config, tmp_path):
    """If a GUID is explicitly provided, it is used."""
    command = WindowsAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    first_app_config.guid = "e822176f-b755-589f-849c-6c6600f7efb1"
    context = command.output_format_template_context(first_app_config)

    # Explicitly provided GUID is used.
    assert context["guid"] == "e822176f-b755-589f-849c-6c6600f7efb1"


def test_support_package_url(first_app_config, tmp_path):
    command = WindowsAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    assert (
        command.support_package_url(4)
        == f"https://www.python.org/ftp/python/{sys.version_info.major}.{sys.version_info.minor}.4/"
        f"python-{sys.version_info.major}.{sys.version_info.minor}.4-embed-amd64.zip"
    )


def test_default_install_scope(first_app_config, tmp_path):
    """By default, app should be installed per user."""
    command = WindowsAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    context = command.output_format_template_context(first_app_config)

    assert context == {
        "guid": "d666a4f1-c7b7-52cc-888a-3a35a7cc97e5",
        "version_triple": "0.0.1",
        "install_scope": None,
    }


def test_per_machine_install_scope(first_app_config, tmp_path):
    """By default, app should be installed per user."""
    command = WindowsAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    first_app_config.system_installer = True

    context = command.output_format_template_context(first_app_config)

    assert context == {
        "guid": "d666a4f1-c7b7-52cc-888a-3a35a7cc97e5",
        "version_triple": "0.0.1",
        "install_scope": "perMachine",
    }


def test_per_user_install_scope(first_app_config, tmp_path):
    """App can be set to have explicit per-user scope."""
    command = WindowsAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    first_app_config.system_installer = False

    context = command.output_format_template_context(first_app_config)

    assert context == {
        "guid": "d666a4f1-c7b7-52cc-888a-3a35a7cc97e5",
        "version_triple": "0.0.1",
        "install_scope": "perUser",
    }
