def test_open(open_command, first_app, second_app):
    """The open command can be called."""
    # Configure no command line options
    options, _ = open_command.parse_options([])

    open_command(**options)

    # The right sequence of things will be done
    assert open_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App configs have been finalized
        ("finalize-app-config", "first"),
        ("finalize-app-config", "second"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # open the first app
        ("open", "first"),
        # App template is verified
        ("verify-app-template", "second"),
        # App tools are verified
        ("verify-app-tools", "second"),
        # open the second app
        ("open", "second"),
    ]


def test_open_single(open_command, first_app):
    """The open command can be called to open a single app from the config."""
    # Configure no command line options
    options, _ = open_command.parse_options([])

    open_command(app=open_command.apps["first"], **options)

    # The right sequence of things will be done
    assert open_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        # open the first app
        ("open", "first"),
    ]


def test_create_before_open(open_command, tmp_path):
    """If the app doesn't exist, it will be created before opening."""
    # Configure no command line options
    options, _ = open_command.parse_options([])

    open_command(app=open_command.apps["first"], **options)

    # The right sequence of things will be done
    assert open_command.actions == [
        # Host OS is verified
        ("verify-host",),
        # Tools are verified
        ("verify-tools",),
        # App config has been finalized
        ("finalize-app-config", "first"),
        # create, then open the first app
        ("create", "first", {}),
        # App template is verified
        ("verify-app-template", "first"),
        # App tools are verified
        ("verify-app-tools", "first"),
        ("open", "first"),
    ]
