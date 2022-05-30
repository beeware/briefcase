import sys

import pytest

from briefcase.platforms.windows.msi import WindowsMSICreateCommand


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
    command = WindowsMSICreateCommand(base_path=tmp_path)

    first_app_config.version = version
    context = command.output_format_template_context(first_app_config)

    assert context["version_triple"] == version_triple


def test_explicit_version_triple(first_app_config, tmp_path):
    command = WindowsMSICreateCommand(base_path=tmp_path)

    first_app_config.version = "1.2.3a1"
    first_app_config.version_triple = "2.3.4"

    context = command.output_format_template_context(first_app_config)

    # Explicit version triple is used.
    assert context["version_triple"] == "2.3.4"


def test_guid(first_app_config, tmp_path):
    """A preictable GUID will be generated from the bundle."""
    command = WindowsMSICreateCommand(base_path=tmp_path)

    context = command.output_format_template_context(first_app_config)

    assert context["guid"] == "d666a4f1-c7b7-52cc-888a-3a35a7cc97e5"


def test_explicit_guid(first_app_config, tmp_path):
    """If a GUID is explicitly provided, it is used."""
    command = WindowsMSICreateCommand(base_path=tmp_path)

    first_app_config.guid = "e822176f-b755-589f-849c-6c6600f7efb1"
    context = command.output_format_template_context(first_app_config)

    # Explicitly provided GUID is used.
    assert context["guid"] == "e822176f-b755-589f-849c-6c6600f7efb1"


def test_support_package_url(first_app_config, tmp_path):
    command = WindowsMSICreateCommand(base_path=tmp_path)

    # Set some properties of the host system for test purposes.
    command.host_arch = "wonky"
    command.platform = "tester"

    # This test result is dependent on whether we're using a 32-bit (win32)
    # or 64-bit (amd64) machine.
    arch = "amd64" if sys.maxsize.bit_length() == 63 else "win32"
    assert command.support_package_url_query == [
        ("platform", "tester"),
        ("version", f"3.{sys.version_info.minor}"),
        ("arch", arch),
    ]


def test_default_install_scope(first_app_config, tmp_path):
    """By default, app should be installed per user."""
    command = WindowsMSICreateCommand(base_path=tmp_path)

    context = command.output_format_template_context(first_app_config)

    assert context["install_scope"] == "perUser"


def test_per_machine_install_scope(first_app_config, tmp_path):
    """By default, app should be installed per user."""
    command = WindowsMSICreateCommand(base_path=tmp_path)
    first_app_config.system_installer = True

    context = command.output_format_template_context(first_app_config)

    assert context["install_scope"] == "perMachine"


def test_per_user_install_scope(first_app_config, tmp_path):
    """App can be set to have explocit per-user scope."""
    command = WindowsMSICreateCommand(base_path=tmp_path)
    first_app_config.system_installer = False

    context = command.output_format_template_context(first_app_config)

    assert context["install_scope"] == "perUser"
