
def test_update_app(update_command, first_app):
    "If the app already exists, it will be updated"
    update_command.update_app(update_command.apps['first'])

    # The right sequence of things will be done
    assert update_command.actions == [
        ('dependencies', update_command.apps['first']),
        ('code', update_command.apps['first']),
    ]

    # App content has been updated
    assert (update_command.platform_path / 'first.dummy' / 'dependencies').exists()
    assert (update_command.platform_path / 'first.dummy' / 'code.py').exists()
    # ... and the app still exists
    assert (update_command.platform_path / 'first.dummy' / 'Content').exists()


def test_update_non_existing_app(update_command):
    "If the app hasn't been generated yet, it won't be created"

    update_command.update_app(update_command.apps['first'])

    # No app creation actions will be performed
    assert update_command.actions == []

    # App content has been not updated
    assert not (update_command.platform_path / 'first.dummy' / 'dependencies').exists()
    assert not (update_command.platform_path / 'first.dummy' / 'code.py').exists()
