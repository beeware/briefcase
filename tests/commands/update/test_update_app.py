
def test_update_app(update_command, first_app):
    "If the app already exists, it will be updated"
    update_command.update_app(update_command.apps['first'])

    # The right sequence of things will be done
    assert update_command.actions == [
        ('code', update_command.apps['first']),
    ]

    # App content and extras have been updated
    assert (update_command.platform_path / 'first.dummy' / 'code.py').exists()
    # Dependencies and extras haven't been updated
    assert not (update_command.platform_path / 'first.dummy' / 'dependencies').exists()
    assert not (update_command.platform_path / 'first.dummy' / 'extras').exists()
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


def test_update_app_with_dependencies(update_command, first_app):
    "If the user requests a dependency update, they are updated"
    update_command.update_app(
        update_command.apps['first'],
        update_dependencies=True,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ('dependencies', update_command.apps['first']),
        ('code', update_command.apps['first']),
    ]

    # App content has been updated
    assert (update_command.platform_path / 'first.dummy' / 'dependencies').exists()
    assert (update_command.platform_path / 'first.dummy' / 'code.py').exists()
    # Extras haven't been updated
    assert not (update_command.platform_path / 'first.dummy' / 'extras').exists()
    # ... and the app still exists
    assert (update_command.platform_path / 'first.dummy' / 'Content').exists()


def test_update_app_with_extras(update_command, first_app):
    "If the user requests an extras update, they are updated"
    update_command.update_app(
        update_command.apps['first'],
        update_extras=True,
    )

    # The right sequence of things will be done
    assert update_command.actions == [
        ('code', update_command.apps['first']),
        ('extras', update_command.apps['first']),
    ]

    # App content and extras have been updated
    assert (update_command.platform_path / 'first.dummy' / 'code.py').exists()
    assert (update_command.platform_path / 'first.dummy' / 'extras').exists()
    # Dependencies haven't been updated
    assert not (update_command.platform_path / 'first.dummy' / 'dependencies').exists()
    # ... and the app still exists
    assert (update_command.platform_path / 'first.dummy' / 'Content').exists()
