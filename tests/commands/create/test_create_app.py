from unittest import mock


def test_create_app(tracking_create_command):
    "If the app doesn't already exist, it will be created"
    tracking_create_command.create_app(tracking_create_command.apps['first'])

    # The right sequence of things will be done
    assert tracking_create_command.actions == [
        ('generate', tracking_create_command.apps['first']),
        ('support', tracking_create_command.apps['first']),
        ('dependencies', tracking_create_command.apps['first']),
        ('code', tracking_create_command.apps['first']),
        ('resources', tracking_create_command.apps['first']),
    ]

    # New app content has been created
    assert (tracking_create_command.platform_path / 'first.bundle' / 'new').exists()


def test_create_existing_app_overwrite(tracking_create_command):
    "An existing app can be overwritten if requested"
    # Answer yes when asked
    tracking_create_command.input = mock.MagicMock(return_value='y')

    # Generate an app in the location.
    bundle_path = tracking_create_command.platform_path / 'first.bundle'
    bundle_path.mkdir(parents=True)
    with (bundle_path / 'original').open('w') as f:
        f.write('original template!')

    tracking_create_command.create_app(tracking_create_command.apps['first'])

    # The right sequence of things will be done
    assert tracking_create_command.actions == [
        ('generate', tracking_create_command.apps['first']),
        ('support', tracking_create_command.apps['first']),
        ('dependencies', tracking_create_command.apps['first']),
        ('code', tracking_create_command.apps['first']),
        ('resources', tracking_create_command.apps['first']),
    ]

    # Original content has been deleted
    assert not (bundle_path / 'original').exists()

    # New app content has been created
    assert (bundle_path / 'new').exists()


def test_create_existing_app_no_overwrite(tracking_create_command):
    "If you say no, the existing app won't be overwritten"
    # Answer no when asked
    tracking_create_command.input = mock.MagicMock(return_value='n')

    bundle_path = tracking_create_command.platform_path / 'first.bundle'
    bundle_path.mkdir(parents=True)
    with (bundle_path / 'original').open('w') as f:
        f.write('original template!')

    tracking_create_command.create_app(tracking_create_command.apps['first'])

    # No app creation actions will be performed
    assert tracking_create_command.actions == []

    # Original content still exists
    assert (bundle_path / 'original').exists()

    # New app content has not been created
    assert not (bundle_path / 'new').exists()


def test_create_existing_app_no_overwrite_default(tracking_create_command):
    "By default, the existing app won't be overwritten"
    # Answer '' (i.e., just press return) when asked
    tracking_create_command.input = mock.MagicMock(return_value='')

    bundle_path = tracking_create_command.platform_path / 'first.bundle'
    bundle_path.mkdir(parents=True)
    with (bundle_path / 'original').open('w') as f:
        f.write('original template!')

    tracking_create_command.create_app(tracking_create_command.apps['first'])

    assert tracking_create_command.actions == []

    # Original content still exists
    assert (bundle_path / 'original').exists()

    # New app content has not been created
    assert not (bundle_path / 'new').exists()
