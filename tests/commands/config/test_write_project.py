from unittest.mock import Mock

import pytest
import tomli

from briefcase.commands.config import ConfigCommand


@pytest.fixture
def config_command(tmp_path):
    tools = Mock()
    tools.base_path = None
    tools.host_os = "Windows"
    tools.input = Mock()
    console = Mock()
    return ConfigCommand(tools=tools, console=console)


@pytest.mark.parametrize(
    "key,value,expected",
    [
        ("author.name", "Jane Smith", {"author": {"name": "Jane Smith"}}),
        ("author.email", "jane@example.com", {"author": {"email": "jane@example.com"}}),
        (
            "macOS.identity",
            "Apple Dev: Jane (TEAM123)",
            {"macOS": {"identity": "Apple Dev: Jane (TEAM123)"}},
        ),
        ("iOS.identity", "iOS Signing Cert", {"iOS": {"identity": "iOS Signing Cert"}}),
        ("android.device", "Pixel_5", {"android": {"device": "Pixel_5"}}),
        ("windows.identity", "Windows Cert", {"windows": {"identity": "Windows Cert"}}),
        ("linux.identity", "Linux Cert", {"linux": {"identity": "Linux Cert"}}),
    ],
)
def test_write_project_config(
    config_command, monkeypatch, tmp_path, key, value, expected
):
    # Simulate running inside a valid Briefcase project
    monkeypatch.chdir(tmp_path)

    # Create a minimal valid pyproject.toml
    (tmp_path / "pyproject.toml").write_text(
        "[tool.briefcase]\nproject_name = 'test'\n", encoding="utf-8"
    )

    config_command.__call__(key=key, value=value, global_config=False)

    # Load and verify the project-level config
    config_path = tmp_path / ".briefcase" / "config.toml"
    with config_path.open("rb") as f:
        config = tomli.load(f)

    assert config == expected
