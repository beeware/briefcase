from unittest.mock import MagicMock

import pytest

from briefcase.commands.run import RunCommand

from .conftest import DummyRunCommand


@pytest.mark.parametrize(
    "platform,expected_devices",
    [
        ("iOS", ["iPhone 14", "iPhone 15", "iPhone 16"]),
        ("android", ["Pixel_5", "Nexus_5X_API_28", "Galaxy_Nexus_API_27"]),
        ("wearos", ["WearOS_3", "WearOS_4"]),
        ("macOS", []),
    ],
)
def test_get_device_choices(platform, expected_devices):
    command = DummyRunCommand()
    command.platform = platform
    command.get_device_choices = RunCommand.get_device_choices.__get__(command)
    assert command.get_device_choices() == expected_devices


@pytest.mark.parametrize(
    "cli_value,config_value,prompt_value,expected",
    [
        ("iPhone 16", None, None, "iPhone 16"),
        (None, "iPhone 15", None, "iPhone 15"),
        ("?", None, "Prompted Device", "Prompted Device"),
    ],
)
def test_get_run_device(monkeypatch, cli_value, config_value, prompt_value, expected):
    command = DummyRunCommand()
    command.platform = "iOS"
    command.get_device_choices = lambda: ["iPhone 14", "iPhone 15", "iPhone 16"]
    command.get_run_device = RunCommand.get_run_device.__get__(command)

    command.tools.config = MagicMock()
    command.tools.input = MagicMock()
    command.tools.config.get.return_value = config_value or expected
    command.tools.input.selection.return_value = prompt_value or expected

    result = command.get_run_device(cli_value=cli_value)
    assert result == expected
