from .conftest import DummyCommand


def test_briefcase_required_python_version(base_command):
    assert base_command.briefcase_required_python_version == (3, 9)


def test_bundle_path(base_command, my_app, tmp_path):
    bundle_path = base_command.bundle_path(my_app)

    assert bundle_path == tmp_path / "base_path/build/my-app/tester/dummy"


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
    command.tools.console.input_enabled = False

    # Check the enabled state of subcommands
    assert not command.create_command.console.input_enabled
    assert command.create_command.console is command.tools.console
    assert command.create_command.tools is command.tools
    assert command.create_command.is_clone is True

    assert not command.update_command.console.input_enabled
    assert command.update_command.console is command.tools.console
    assert command.update_command.tools is command.tools
    assert command.update_command.is_clone is True

    assert not command.build_command.console.input_enabled
    assert command.build_command.console is command.tools.console
    assert command.build_command.tools is command.tools
    assert command.build_command.is_clone is True

    assert not command.run_command.console.input_enabled
    assert command.run_command.console is command.tools.console
    assert command.run_command.tools is command.tools
    assert command.run_command.is_clone is True

    assert not command.package_command.console.input_enabled
    assert command.package_command.console is command.tools.console
    assert command.package_command.tools is command.tools
    assert command.package_command.is_clone is True

    assert not command.publish_command.console.input_enabled
    assert command.publish_command.console is command.tools.console
    assert command.publish_command.tools is command.tools
    assert command.publish_command.is_clone is True
