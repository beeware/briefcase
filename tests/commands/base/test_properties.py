
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


def test_publish_command(base_command):
    # Check for a property of the created command class.
    assert base_command.publish_command.description == "Test Publish"
