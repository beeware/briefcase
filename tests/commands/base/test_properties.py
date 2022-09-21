from .conftest import DummyCommand


def test_bundle_path(base_command, my_app, tmp_path):
    bundle_path = base_command.bundle_path(my_app)

    assert bundle_path == tmp_path / "tester" / "dumdum" / "My App"


def test_create_command(base_command):
    # Check for a property of the created command class.
    assert base_command.create_command.description == "Test Create"


def test_update_command(base_command):
    # Check for a property of the created command class.
    assert base_command.update_command.description == "Test Update"


def test_build_command(base_command):
    # Check for a property of the created command class.
    assert base_command.build_command.description == "Test Build"


def test_run_command(base_command):
    # Check for a property of the created command class.
    assert base_command.run_command.description == "Test Run"


def test_package_command(base_command):
    # Check for a property of the created command class.
    assert base_command.package_command.description == "Test Package"


def test_publish_command(base_command):
    # Check for a property of the created command class.
    assert base_command.publish_command.description == "Test Publish"


def test_command_state_transferred(tmp_path):
    """Command state is transferred to created subcommands."""
    command = DummyCommand(base_path=tmp_path)
    command.tools.input.enabled = False

    # Check the enabled state of subcommands
    assert not command.create_command.input.enabled
    assert command.create_command.logger is command.tools.logger
    assert command.create_command.input is command.tools.input
    assert command.create_command.tools is command.tools
    assert command.create_command.is_clone is True

    assert not command.update_command.input.enabled
    assert command.update_command.logger is command.tools.logger
    assert command.update_command.input is command.tools.input
    assert command.update_command.tools is command.tools
    assert command.update_command.is_clone is True

    assert not command.build_command.input.enabled
    assert command.build_command.logger is command.tools.logger
    assert command.build_command.input is command.tools.input
    assert command.build_command.tools is command.tools
    assert command.build_command.is_clone is True

    assert not command.run_command.input.enabled
    assert command.run_command.logger is command.tools.logger
    assert command.run_command.input is command.tools.input
    assert command.run_command.tools is command.tools
    assert command.run_command.is_clone is True

    assert not command.package_command.input.enabled
    assert command.package_command.logger is command.tools.logger
    assert command.package_command.input is command.tools.input
    assert command.package_command.tools is command.tools
    assert command.package_command.is_clone is True

    assert not command.publish_command.input.enabled
    assert command.publish_command.logger is command.tools.logger
    assert command.publish_command.input is command.tools.input
    assert command.publish_command.tools is command.tools
    assert command.publish_command.is_clone is True
