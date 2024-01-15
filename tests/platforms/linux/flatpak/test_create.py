from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseConfigError, UnsupportedHostError
from briefcase.integrations.flatpak import Flatpak
from briefcase.platforms.linux.flatpak import LinuxFlatpakCreateCommand


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
