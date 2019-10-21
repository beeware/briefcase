
def test_update_app(update_command, tmp_path, first_app):
    "If the app already exists, it will be updated"
    update_command.update_app(update_command.apps['first'], tmp_path)

    # The right sequence of things will be done
    assert update_command.actions == [
        ('dependencies', update_command.apps['first'], tmp_path),
        ('code', update_command.apps['first'], tmp_path),
    ]

    # App content has been updated
    assert (tmp_path / 'tester' / 'first.dummy' / 'dependencies').exists()
    assert (tmp_path / 'tester' / 'first.dummy' / 'code.py').exists()


def test_update_non_existing_app(update_command, tmp_path):
    "If the app hasn't been generated yet, it won't be created"

    update_command.update_app(update_command.apps['first'], tmp_path)

    # No app creation actions will be performed
    assert update_command.actions == []

    # App content has been not updated
    assert not (tmp_path / 'tester' / 'first.dummy' / 'dependencies').exists()
    assert not (tmp_path / 'tester' / 'first.dummy' / 'code.py').exists()
