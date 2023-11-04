from unittest.mock import PropertyMock


def test_supported_encoding(base_command, capsys, monkeypatch):
    """User is not warned for a supported encoding."""
    monkeypatch.setattr(
        type(base_command.tools), "system_encoding", PropertyMock(return_value="UTF-8")
    )
    base_command.validate_locale()
    assert "Default system encoding is not supported" not in capsys.readouterr().out


def test_unsupported_encoding(base_command, capsys, monkeypatch):
    """User is warned for an unsupported encoding on Linux."""
    base_command.tools.host_os = "Linux"
    monkeypatch.setattr(
        type(base_command.tools),
        "system_encoding",
        PropertyMock(return_value="ISO-NOPE"),
    )
    base_command.validate_locale()
    assert "Default system encoding is not supported" in capsys.readouterr().out
