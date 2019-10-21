from .test_create_app import create_command


def test_create(create_command):
    "The create command can be called"
    create_command()

    # The right sequence of things will be done
    assert create_command.actions == [
        ('verify'),

        # Create the first app
        ('generate', create_command.apps['first']),
        ('support', create_command.apps['first']),
        ('dependencies', create_command.apps['first']),
        ('code', create_command.apps['first']),
        ('extras', create_command.apps['first']),

        # Create the second app
        ('generate', create_command.apps['second']),
        ('support', create_command.apps['second']),
        ('dependencies', create_command.apps['second']),
        ('code', create_command.apps['second']),
        ('extras', create_command.apps['second']),
    ]

    # New app content has been created
    assert (create_command.platform_path / 'first.dummy' / 'new').exists()
    assert (create_command.platform_path / 'second.dummy' / 'new').exists()


def test_create_single(create_command):
    "The create command can be called to create a single app from the config"
    create_command(app=create_command.apps['first'])

    # The right sequence of things will be done
    assert create_command.actions == [
        ('verify'),

        # Create the first app
        ('generate', create_command.apps['first']),
        ('support', create_command.apps['first']),
        ('dependencies', create_command.apps['first']),
        ('code', create_command.apps['first']),
        ('extras', create_command.apps['first']),
    ]

    # New app content has been created
    assert (create_command.platform_path / 'first.dummy' / 'new').exists()
    assert not (create_command.platform_path / 'second.dummy' / 'new').exists()
