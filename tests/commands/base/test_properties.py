
def test_create_command(base_command):
    # Check for a property of the created command class.
    assert base_command.CreateCommand.description == "Test Create"


def test_update_command(base_command):
    # Check for a property of the created command class.
    assert base_command.UpdateCommand.description == "Test Update"


def test_build_command(base_command):
    # Check for a property of the created command class.
    assert base_command.BuildCommand.description == "Test Build"


def test_run_command(base_command):
    # Check for a property of the created command class.
    assert base_command.RunCommand.description == "Test Run"


def test_publish_command(base_command):
    # Check for a property of the created command class.
    assert base_command.PublishCommand.description == "Test Publish"
