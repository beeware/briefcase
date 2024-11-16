import datetime
from unittest import mock
from unittest.mock import MagicMock

import pytest
import tomli_w

import briefcase.commands
import briefcase.platforms.linux.flatpak
from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseConfigError, UnsupportedHostError
from briefcase.integrations.flatpak import Flatpak
from briefcase.platforms.linux.flatpak import LinuxFlatpakCreateCommand


@pytest.fixture
def mock_now(monkeypatch):
    """Monkeypatch the ``datetime.now`` inside ``briefcase.commands.create``.

    When this fixture is used, the datetime is locked to 2024 May 2 @ 12:00:00:000500.
    """
    now = datetime.datetime(2024, 5, 2, 12, 0, 0, 500)
    datetime_mock = mock.MagicMock(wraps=datetime.datetime)
    datetime_mock.now.return_value = now
    monkeypatch.setattr(briefcase.commands.create, "datetime", datetime_mock)
    monkeypatch.setattr(briefcase.platforms.linux.flatpak, "datetime", datetime_mock)
    return now


@pytest.fixture
def create_command(tmp_path):
    return LinuxFlatpakCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


@pytest.mark.parametrize("host_os", ["Darwin", "Windows", "WeirdOS"])
def test_unsupported_host_os(create_command, host_os):
    """Error raised for an unsupported OS."""
    create_command.tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match="Flatpaks can only be built on Linux.",
    ):
        create_command()


def test_output_format_template_context(create_command, first_app_config):
    """The template context is provided flatpak details."""
    first_app_config.flatpak_runtime = "org.beeware.Platform"
    first_app_config.flatpak_runtime_version = "37.42"
    first_app_config.flatpak_sdk = "org.beeware.SDK"

    assert create_command.output_format_template_context(first_app_config) == {
        "flatpak_runtime": "org.beeware.Platform",
        "flatpak_runtime_version": "37.42",
        "flatpak_sdk": "org.beeware.SDK",
    }


DEFAULT_FINISH_ARGS = {
    "share=ipc": True,
    "socket=x11": True,
    "nosocket=wayland": True,
    "share=network": True,
    "device=dri": True,
    "socket=pulseaudio": True,
    "filesystem=xdg-cache": True,
    "filesystem=xdg-config": True,
    "filesystem=xdg-data": True,
    "filesystem=xdg-documents": True,
    "socket=session-bus": True,
}


@pytest.mark.parametrize(
    "permissions, finish_args, context",
    [
        # No permissions
        (
            {},
            {},
            {
                "finish_args": DEFAULT_FINISH_ARGS,
            },
        ),
        # Only custom permissions
        (
            {
                "custom_permission": "Custom message",
            },
            {
                "allow=bluetooth": True,
            },
            {
                "finish_args": {
                    "share=ipc": True,
                    "socket=x11": True,
                    "nosocket=wayland": True,
                    "share=network": True,
                    "device=dri": True,
                    "socket=pulseaudio": True,
                    "filesystem=xdg-cache": True,
                    "filesystem=xdg-config": True,
                    "filesystem=xdg-data": True,
                    "filesystem=xdg-documents": True,
                    "socket=session-bus": True,
                    "allow=bluetooth": True,
                },
            },
        ),
        # Camera permissions
        (
            {
                "camera": "I need to see you",
            },
            {},
            {
                "finish_args": DEFAULT_FINISH_ARGS,
            },
        ),
        # Microphone permissions
        (
            {
                "microphone": "I need to hear you",
            },
            {},
            {
                "finish_args": DEFAULT_FINISH_ARGS,
            },
        ),
        # Coarse location permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
            },
            {},
            {
                "finish_args": DEFAULT_FINISH_ARGS,
            },
        ),
        # Fine location permissions
        (
            {
                "fine_location": "I need to know exactly where you are",
            },
            {},
            {
                "finish_args": DEFAULT_FINISH_ARGS,
            },
        ),
        # Background location permissions
        (
            {
                "background_location": "I always need to know where you are",
            },
            {},
            {
                "finish_args": DEFAULT_FINISH_ARGS,
            },
        ),
        # Coarse location background permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
                "background_location": "I always need to know where you are",
            },
            {},
            {
                "finish_args": DEFAULT_FINISH_ARGS,
            },
        ),
        # Fine location background permissions
        (
            {
                "fine_location": "I need to know exactly where you are",
                "background_location": "I always need to know where you are",
            },
            {},
            {
                "finish_args": DEFAULT_FINISH_ARGS,
            },
        ),
        # Coarse and fine location permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
                "fine_location": "I need to know exactly where you are",
            },
            {},
            {
                "finish_args": DEFAULT_FINISH_ARGS,
            },
        ),
        # Coarse and fine background location permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
                "fine_location": "I need to know exactly where you are",
                "background_location": "I always need to know where you are",
            },
            {},
            {
                "finish_args": DEFAULT_FINISH_ARGS,
            },
        ),
        # Photo library permissions
        (
            {
                "photo_library": "I need to see your library",
            },
            {},
            {
                "finish_args": DEFAULT_FINISH_ARGS,
            },
        ),
        # Override and augment by cross-platform definitions
        (
            {
                "fine_location": "I need to know where you are",
                "NSCustomMessage": "Custom message",
            },
            {
                "socket=pulseaudio": False,
                "allow=bluetooth": True,
            },
            {
                "finish_args": {
                    "share=ipc": True,
                    "socket=x11": True,
                    "nosocket=wayland": True,
                    "share=network": True,
                    "device=dri": True,
                    "socket=pulseaudio": False,
                    "filesystem=xdg-cache": True,
                    "filesystem=xdg-config": True,
                    "filesystem=xdg-data": True,
                    "filesystem=xdg-documents": True,
                    "socket=session-bus": True,
                    "allow=bluetooth": True,
                },
            },
        ),
    ],
)
def test_permissions_context(
    create_command, first_app, permissions, finish_args, context
):
    """Platform-specific permissions can be added to the context."""
    # Set the permission and entitlement value
    first_app.permission = permissions
    first_app.finish_arg = finish_args
    # Extract the cross-platform permissions
    x_permissions = create_command._x_permissions(first_app)
    # Check that the final platform permissions are rendered as expected.
    assert context == create_command.permissions_context(first_app, x_permissions)


def test_missing_runtime_config(create_command, first_app_config):
    """The app creation errors is a Flatpak runtime is not defined."""
    create_command.tools.flatpak = MagicMock(spec_set=Flatpak)

    with pytest.raises(
        BriefcaseConfigError,
        match="Briefcase configuration error: The App does not specify the Flatpak runtime to use",
    ):
        create_command.output_format_template_context(first_app_config)


BASE_PIP_INSTALL_COMMAND = (
    "/app/bin/python3 -m pip install --no-cache-dir -r requirements.txt"
    ' --target="$INSTALL_TARGET"'
)


@pytest.fixture
def bundle_path(create_command, first_app_config):
    path = create_command.bundle_path(first_app_config)
    path.mkdir(exist_ok=True, parents=True)
    return path


@pytest.fixture
def requirements_path(bundle_path):
    return bundle_path / "requirements.txt"


@pytest.fixture
def install_requirements_path(bundle_path):
    return bundle_path / "install_requirements.sh"


@pytest.fixture
def app_requirements_path_index(bundle_path):
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "src/app",
                "app_requirements_path": "requirements.txt",
                "support_path": "support",
                "support_revision": 37,
            }
        }
        tomli_w.dump(index, f)


def test_install_app_requirements_no_installer_args(
    create_command,
    first_app_config,
    mock_now,
    requirements_path,
    install_requirements_path,
    bundle_path,
    app_requirements_path_index,
):
    """``install_requirements.sh`` is written with base command if app has no requirement
    installer args."""

    first_app_config.requirement_installer_args = []
    first_app_config.requires = []

    create_command.install_app_requirements(first_app_config, test_mode=False)

    assert requirements_path.read_text(encoding="utf-8") == f"# Generated {mock_now}\n"

    assert (
        install_requirements_path.read_text(encoding="utf-8")
        == f"# Generated {mock_now}\n{BASE_PIP_INSTALL_COMMAND}\n"
    )


def test_install_app_requirements_with_requires(
    create_command,
    first_app_config,
    mock_now,
    requirements_path,
    install_requirements_path,
    bundle_path,
    app_requirements_path_index,
):
    """``requirements.txt`` is written with requirements if app has requires."""
    # This test confirms Flatpak create command is still writing requirements.txt as in the base command
    # It does not extensively test this behaviour because it's already tested by the create command tests
    # This only serves as confirmation that it's still operating for the Flatpak version of the command

    first_app_config.requirement_installer_args = ["-fwheels"]
    first_app_config.requires = ["first-package==0.2.1", "second"]

    create_command.install_app_requirements(first_app_config, test_mode=False)

    assert (
        requirements_path.read_text(encoding="utf-8")
        == f"# Generated {mock_now}\nfirst-package==0.2.1\nsecond\n"
    )

    assert (
        install_requirements_path.read_text(encoding="utf-8")
        == f"# Generated {mock_now}\n{BASE_PIP_INSTALL_COMMAND} -fwheels\n"
    )


def test_install_app_requirements_with_installer_args(
    create_command,
    first_app_config,
    mock_now,
    requirements_path,
    install_requirements_path,
    bundle_path,
    app_requirements_path_index,
):
    """``install_requirements.sh`` is written with base command and additional
    arguments if app has requirement installer args."""

    first_app_config.requirement_installer_args = ["--arbitrary-extra-argument"]
    first_app_config.requires = []

    create_command.install_app_requirements(first_app_config, test_mode=False)

    assert requirements_path.read_text(encoding="utf-8") == f"# Generated {mock_now}\n"

    assert (
        install_requirements_path.read_text(encoding="utf-8")
        == f"# Generated {mock_now}\n{BASE_PIP_INSTALL_COMMAND} --arbitrary-extra-argument\n"
    )


def test_install_app_requirement_installer_args_path_transformation(
    create_command,
    first_app_config,
    mock_now,
    requirements_path,
    install_requirements_path,
    bundle_path,
    app_requirements_path_index,
):
    """``install_requirements.sh`` is written with base command and transformed
    relative paths if app has requirement installer args with relative paths."""

    wheels_path = create_command.base_path / "wheels"
    wheels_path.mkdir(exist_ok=True)
    first_app_config.requirement_installer_args = ["-f", "./wheels"]
    first_app_config.requires = []

    create_command.install_app_requirements(first_app_config, test_mode=False)

    assert requirements_path.read_text(encoding="utf-8") == f"# Generated {mock_now}\n"

    assert (
        install_requirements_path.read_text(encoding="utf-8")
        == f"# Generated {mock_now}\n{BASE_PIP_INSTALL_COMMAND} -f {wheels_path.absolute()}\n"
    )
