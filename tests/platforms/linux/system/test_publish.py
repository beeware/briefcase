from briefcase.platforms.linux.system import LinuxSystemPublishCommand


def test_default_packaging_format(dummy_console, mock_tools, tmp_path):
    """The app's finalized configuration determines the packaging format."""
    command = LinuxSystemPublishCommand(
        console=dummy_console,
        tools=mock_tools,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    assert command.default_packaging_format is None
