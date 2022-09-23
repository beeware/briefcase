def test_specific_app(build_command, first_app, second_app):
    """If a specific app is requested, build it."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options = build_command.parse_options([])

    # Run the build command
    build_command(first_app, **options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # App tools are verified for app
        ("verify-app-tools", "first"),
        # Build the first app; no state
        ("build", "first", {}),
    ]


def test_multiple_apps(build_command, first_app, second_app):
    """If there are multiple apps, build all of them."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure no command line options
    options = build_command.parse_options([])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # Build the first app; no state
        ("build", "first", {}),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # Build the second apps; state from previous build.
        ("build", "second", {"build_state": "first"}),
    ]


def test_non_existent(build_command, first_app_config, second_app):
    """Requesting a build of a non-existent app causes a create."""
    # Add two apps; use the "config only" version of the first app.
    build_command.apps = {
        "first": first_app_config,
        "second": second_app,
    }

    # Configure no command line options
    options = build_command.parse_options([])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # First App doesn't exist, so it will be created, then built
        ("create", "first", {}),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"create_state": "first"}),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # Second app *does* exist, so it only be built
        ("build", "second", {"create_state": "first", "build_state": "first"}),
    ]


def test_unbuilt(build_command, first_app_unbuilt, second_app):
    """Requesting a build of an app that has been created, but not build, just
    causes a build."""
    # Add two apps; use the "unbuilt" version of the first app.
    build_command.apps = {
        "first": first_app_unbuilt,
        "second": second_app,
    }

    # Configure no command line options
    options = build_command.parse_options([])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        # First App exists, but hasn't been built; it will be built.
        ("build", "first", {}),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # Second app has been built before; it will be built again.
        ("build", "second", {"build_state": "first"}),
    ]


def test_update_app(build_command, first_app, second_app):
    """If an update is requested, app is updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure a -a command line option
    options = build_command.parse_options(["-u"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # Update then build the first app
        ("update", "first", {}),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"update_state": "first"}),
        # Update then build the second app
        ("update", "second", {"update_state": "first", "build_state": "first"}),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        ("build", "second", {"update_state": "second", "build_state": "first"}),
    ]


def test_update_non_existent(build_command, first_app_config, second_app):
    """Requesting an update of a non-existent app causes a create."""
    # Add two apps; use the "config only" version of the first app.
    build_command.apps = {
        "first": first_app_config,
        "second": second_app,
    }

    # Configure no command line options
    options = build_command.parse_options(["-u"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # First App doesn't exist, so it will be created, then built
        ("create", "first", {}),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"create_state": "first"}),
        # Second app *does* exist, so it will be updated, then built
        ("update", "second", {"create_state": "first", "build_state": "first"}),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            {"create_state": "first", "build_state": "first", "update_state": "second"},
        ),
    ]


def test_update_unbuilt(build_command, first_app_unbuilt, second_app):
    """Requesting an update of an upbuilt app causes an update before build."""
    # Add two apps; use the "unbuilt" version of the first app.
    build_command.apps = {
        "first": first_app_unbuilt,
        "second": second_app,
    }

    # Configure no command line options
    options = build_command.parse_options(["-u"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # First App exists, but hasn't been built; it will be updated then built.
        ("update", "first", {}),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"update_state": "first"}),
        # Second app has been built before; it will be built again.
        ("update", "second", {"update_state": "first", "build_state": "first"}),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        ("build", "second", {"update_state": "second", "build_state": "first"}),
    ]
