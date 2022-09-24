def test_open(open_command, first_app, second_app):
    """The open command can be called."""
    # Configure no command line options
    options = open_command.parse_options([])

    open_command(**options)

    # The right sequence of things will be done
    assert open_command.actions == [
        ("verify",),
        ("verify-app-tools", "first"),
        # open the first app
        ("open", first_app),
        ("verify-app-tools", "second"),
        # open the second app
        ("open", second_app),
    ]


def test_open_single(open_command, first_app):
    """The open command can be called to open a single app from the config."""
    # Configure no command line options
    options = open_command.parse_options([])

    open_command(app=open_command.apps["first"], **options)

    # The right sequence of things will be done
    assert open_command.actions == [
        ("verify",),
        ("verify-app-tools", "first"),
        # open the first app
        ("open", first_app),
    ]


def test_create_before_open(open_command, tmp_path):
    """If the app doesn't exist, it will be created before opening."""
    # Configure no command line options
    options = open_command.parse_options([])

    open_command(app=open_command.apps["first"], **options)

    # The right sequence of things will be done
    assert open_command.actions == [
        ("verify",),
        # create, then open the first app
        ("create", "first", {}),
        ("verify-app-tools", "first"),
        ("open", tmp_path / "tester" / "dummy" / "first" / "first.project"),
    ]
