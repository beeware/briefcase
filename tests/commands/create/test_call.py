from .test_create_app import create_command


def test_create(create_command, tmp_path):
    "The create command can be called"
    bundle_path = tmp_path / 'tester'

    create_command(path=tmp_path)

    # The right sequence of things will be done
    assert create_command.actions == [
        ('verify'),

        # Create the first app
        ('generate', create_command.apps['first'], tmp_path),
        ('support', create_command.apps['first'], tmp_path),
        ('dependencies', create_command.apps['first'], tmp_path),
        ('code', create_command.apps['first'], tmp_path),
        ('extras', create_command.apps['first'], tmp_path),

        # Create the second app
        ('generate', create_command.apps['second'], tmp_path),
        ('support', create_command.apps['second'], tmp_path),
        ('dependencies', create_command.apps['second'], tmp_path),
        ('code', create_command.apps['second'], tmp_path),
        ('extras', create_command.apps['second'], tmp_path),
    ]

    # New app content has been created
    assert (bundle_path / 'first.dummy' / 'new').exists()
    assert (bundle_path / 'second.dummy' / 'new').exists()


def test_create_single(create_command, tmp_path):
    "The create command can be called to create a single app from the config"
    bundle_path = tmp_path / 'tester'

    create_command(app=create_command.apps['first'], path=tmp_path)

    # The right sequence of things will be done
    assert create_command.actions == [
        ('verify'),

        # Create the first app
        ('generate', create_command.apps['first'], tmp_path),
        ('support', create_command.apps['first'], tmp_path),
        ('dependencies', create_command.apps['first'], tmp_path),
        ('code', create_command.apps['first'], tmp_path),
        ('extras', create_command.apps['first'], tmp_path),

    ]

    # New app content has been created
    assert (bundle_path / 'first.dummy' / 'new').exists()
    assert not (bundle_path / 'second.dummy' / 'new').exists()
