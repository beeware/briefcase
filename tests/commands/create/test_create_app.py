from unittest import mock


def test_create_app(tracking_create_command):
    "If the app doesn't already exist, it will be created"
    tracking_create_command.create_app(tracking_create_command.apps['first'])

    # The right sequence of things will be done
    assert tracking_create_command.actions == [
        ('check_bundle_path_existence', tracking_create_command.apps['first'], None),
        ('generate', tracking_create_command.apps['first']),
        ('support', tracking_create_command.apps['first']),
        ('dependencies', tracking_create_command.apps['first']),
        ('code', tracking_create_command.apps['first']),
        ('resources', tracking_create_command.apps['first']),
    ]

    # New app content has been created
    assert (tracking_create_command.platform_path / 'first.bundle' / 'new').exists()


def test_create_existing_app_override_from_user_input(tracking_create_command):
    "An existing app can be overwritten if requested from user input"
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
        ('check_bundle_path_existence', tracking_create_command.apps['first'], None),
        ('generate', tracking_create_command.apps['first']),
        ('support', tracking_create_command.apps['first']),
        ('dependencies', tracking_create_command.apps['first']),
        ('code', tracking_create_command.apps['first']),
        ('resources', tracking_create_command.apps['first']),
    ]

    tracking_create_command.input.assert_called_once_with(
        'Application first already exists; overwrite (y/N)? '
    )

    # Original content has been deleted
    assert not (bundle_path / 'original').exists()

    # New app content has been created
    assert (bundle_path / 'new').exists()


def test_create_existing_app_override_from_command_line(tracking_create_command):
    "An existing app can be overwritten if requested from command line"
    # Answer yes when asked
    tracking_create_command.input = mock.MagicMock()

    # Generate an app in the location.
    bundle_path = tracking_create_command.platform_path / 'first.bundle'
    bundle_path.mkdir(parents=True)
    with (bundle_path / 'original').open('w') as f:
        f.write('original template!')

    tracking_create_command.create_app(tracking_create_command.apps['first'],
                                       override=True)

    # The right sequence of things will be done
    assert tracking_create_command.actions == [
        ('check_bundle_path_existence', tracking_create_command.apps['first'], True),
        ('generate', tracking_create_command.apps['first']),
        ('support', tracking_create_command.apps['first']),
        ('dependencies', tracking_create_command.apps['first']),
        ('code', tracking_create_command.apps['first']),
        ('resources', tracking_create_command.apps['first']),
    ]

    tracking_create_command.input.assert_not_called()

    # Original content has been deleted
    assert not (bundle_path / 'original').exists()

    # New app content has been created
    assert (bundle_path / 'new').exists()


def test_create_existing_app_no_override_from_user_input(tracking_create_command):
    "An existing app won't be overwritten if user decided not to"
    # Answer no when asked
    tracking_create_command.input = mock.MagicMock(return_value='n')

    bundle_path = tracking_create_command.platform_path / 'first.bundle'
    bundle_path.mkdir(parents=True)
    with (bundle_path / 'original').open('w') as f:
        f.write('original template!')

    tracking_create_command.create_app(tracking_create_command.apps['first'])

    # No app creation actions will be performed
    assert tracking_create_command.actions == [
        ('check_bundle_path_existence', tracking_create_command.apps['first'], None)
    ]

    tracking_create_command.input.assert_called_once_with(
        'Application first already exists; overwrite (y/N)? '
    )

    # Original content still exists
    assert (bundle_path / 'original').exists()

    # New app content has not been created
    assert not (bundle_path / 'new').exists()


def test_create_existing_app_no_override_from_command_line(tracking_create_command):
    "An existing app won't be overwritten if requested so in the command line"
    # Answer no when asked
    tracking_create_command.input = mock.MagicMock(return_value='n')

    bundle_path = tracking_create_command.platform_path / 'first.bundle'
    bundle_path.mkdir(parents=True)
    with (bundle_path / 'original').open('w') as f:
        f.write('original template!')

    tracking_create_command.create_app(
        tracking_create_command.apps['first'], override=False
    )

    # No app creation actions will be performed
    assert tracking_create_command.actions == [
        ('check_bundle_path_existence', tracking_create_command.apps['first'], False)
    ]

    tracking_create_command.input.assert_not_called()

    # Original content still exists
    assert (bundle_path / 'original').exists()

    # New app content has not been created
    assert not (bundle_path / 'new').exists()


def test_create_existing_app_no_override_default(tracking_create_command):
    "By default, the existing app won't be overwritten"
    # Answer '' (i.e., just press return) when asked
    tracking_create_command.input = mock.MagicMock(return_value='')

    bundle_path = tracking_create_command.platform_path / 'first.bundle'
    bundle_path.mkdir(parents=True)
    with (bundle_path / 'original').open('w') as f:
        f.write('original template!')

    tracking_create_command.create_app(tracking_create_command.apps['first'])

    assert tracking_create_command.actions == [
        ('check_bundle_path_existence', tracking_create_command.apps['first'], None),
    ]

    # Original content still exists
    assert (bundle_path / 'original').exists()

    # New app content has not been created
    assert not (bundle_path / 'new').exists()
