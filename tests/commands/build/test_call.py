import pytest

from briefcase.exceptions import BriefcaseCommandError


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
        ("build", "first", {"test_mode": False}),
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
        ("build", "first", {"test_mode": False}),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # Build the second apps; state from previous build.
        ("build", "second", {"build_state": "first", "test_mode": False}),
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
        ("create", "first", {"test_mode": False}),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"create_state": "first", "test_mode": False}),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # Second app *does* exist, so it only be built
        (
            "build",
            "second",
            {"create_state": "first", "build_state": "first", "test_mode": False},
        ),
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
        ("build", "first", {"test_mode": False}),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        # Second app has been built before; it will be built again.
        ("build", "second", {"build_state": "first", "test_mode": False}),
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
        (
            "update",
            "first",
            {
                "test_mode": False,
                "update_requirements": False,
                "update_resources": False,
            },
        ),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"update_state": "first", "test_mode": False}),
        # Update then build the second app
        (
            "update",
            "second",
            {
                "update_state": "first",
                "build_state": "first",
                "test_mode": False,
                "update_requirements": False,
                "update_resources": False,
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            {"update_state": "second", "build_state": "first", "test_mode": False},
        ),
    ]


def test_update_app_requirements(build_command, first_app, second_app):
    """If a requirements update is requested, app is updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure update command line options
    options = build_command.parse_options(["-r"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # Update then build the first app
        (
            "update",
            "first",
            {
                "test_mode": False,
                "update_requirements": True,
                "update_resources": False,
            },
        ),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"update_state": "first", "test_mode": False}),
        # Update then build the second app
        (
            "update",
            "second",
            {
                "update_state": "first",
                "build_state": "first",
                "test_mode": False,
                "update_requirements": True,
                "update_resources": False,
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            {"update_state": "second", "build_state": "first", "test_mode": False},
        ),
    ]


def test_update_app_resources(build_command, first_app, second_app):
    """If a resources update is requested, app is updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure update command line options
    options = build_command.parse_options(["--update-resources"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # Update then build the first app
        (
            "update",
            "first",
            {
                "test_mode": False,
                "update_requirements": False,
                "update_resources": True,
            },
        ),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"update_state": "first", "test_mode": False}),
        # Update then build the second app
        (
            "update",
            "second",
            {
                "update_state": "first",
                "build_state": "first",
                "test_mode": False,
                "update_requirements": False,
                "update_resources": True,
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            {"update_state": "second", "build_state": "first", "test_mode": False},
        ),
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
        ("create", "first", {"test_mode": False}),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"create_state": "first", "test_mode": False}),
        # Second app *does* exist, so it will be updated, then built
        (
            "update",
            "second",
            {
                "create_state": "first",
                "build_state": "first",
                "test_mode": False,
                "update_requirements": False,
                "update_resources": False,
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            {
                "create_state": "first",
                "build_state": "first",
                "update_state": "second",
                "test_mode": False,
            },
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
        (
            "update",
            "first",
            {
                "test_mode": False,
                "update_requirements": False,
                "update_resources": False,
            },
        ),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"update_state": "first", "test_mode": False}),
        # Second app has been built before; it will be built again.
        (
            "update",
            "second",
            {
                "update_state": "first",
                "build_state": "first",
                "test_mode": False,
                "update_requirements": False,
                "update_resources": False,
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            {"update_state": "second", "build_state": "first", "test_mode": False},
        ),
    ]


def test_build_test(build_command, first_app, second_app):
    """If the user builds a test app, app is updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options = build_command.parse_options(["--test"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # Update then build the first app
        (
            "update",
            "first",
            {
                "test_mode": True,
                "update_requirements": False,
                "update_resources": False,
            },
        ),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"update_state": "first", "test_mode": True}),
        # Update then build the second app
        (
            "update",
            "second",
            {
                "update_state": "first",
                "build_state": "first",
                "test_mode": True,
                "update_requirements": False,
                "update_resources": False,
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            {"update_state": "second", "build_state": "first", "test_mode": True},
        ),
    ]


def test_build_test_no_update(build_command, first_app, second_app):
    """If the user builds a test app without app updates, requirements and
    resources are still updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options = build_command.parse_options(["--test", "--no-update"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # No update of the first app
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"test_mode": True}),
        # No update of the second app
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            {"build_state": "first", "test_mode": True},
        ),
    ]


def test_build_test_update_dependences(build_command, first_app, second_app):
    """If the user builds a test app with app dependency updates, app code and
    resources are updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options = build_command.parse_options(["--test", "-r"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # Update then build the first app
        (
            "update",
            "first",
            {
                "test_mode": True,
                "update_requirements": True,
                "update_resources": False,
            },
        ),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"update_state": "first", "test_mode": True}),
        # Update then build the second app
        (
            "update",
            "second",
            {
                "update_state": "first",
                "build_state": "first",
                "test_mode": True,
                "update_requirements": True,
                "update_resources": False,
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            {"update_state": "second", "build_state": "first", "test_mode": True},
        ),
    ]


def test_build_test_update_resources(build_command, first_app, second_app):
    """If the user builds a test app with app resource updates, app code and
    resources are updated before build."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options = build_command.parse_options(["--test", "--update-resources"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # Update then build the first app
        (
            "update",
            "first",
            {
                "test_mode": True,
                "update_requirements": False,
                "update_resources": True,
            },
        ),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"update_state": "first", "test_mode": True}),
        # Update then build the second app
        (
            "update",
            "second",
            {
                "update_state": "first",
                "build_state": "first",
                "test_mode": True,
                "update_requirements": False,
                "update_resources": True,
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            {"update_state": "second", "build_state": "first", "test_mode": True},
        ),
    ]


def test_build_invalid_update(build_command, first_app, second_app):
    """If the user requests a build with update and no-update, an error is
    raised."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options = build_command.parse_options(["-u", "--no-update"])

    # Run the build command
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Cannot specify both --update and --no-update",
    ):
        build_command(**options)


def test_build_invalid_update_requirements(build_command, first_app, second_app):
    """If the user requests a build with update-requirements and no-update, an
    error is raised."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options = build_command.parse_options(["-r", "--no-update"])

    # Run the build command
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Cannot specify both --update-requirements and --no-update",
    ):
        build_command(**options)


def test_build_invalid_update_resources(build_command, first_app, second_app):
    """If the user requests a build with update-resources and no-update, an
    error is raised."""
    # Add two apps
    build_command.apps = {
        "first": first_app,
        "second": second_app,
    }

    # Configure command line options
    options = build_command.parse_options(["--update-resources", "--no-update"])

    # Run the build command
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Cannot specify both --update-resources and --no-update",
    ):
        build_command(**options)


def test_test_app_non_existent(build_command, first_app_config, second_app):
    """Requesting an test build of a non-existent app causes a create."""
    # Add two apps; use the "config only" version of the first app.
    build_command.apps = {
        "first": first_app_config,
        "second": second_app,
    }

    # Configure command line options
    options = build_command.parse_options(["-u", "--test"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # First App doesn't exist, so it will be created, then built
        ("create", "first", {"test_mode": True}),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        ("build", "first", {"create_state": "first", "test_mode": True}),
        # Second app *does* exist, so it will be updated, then built
        (
            "update",
            "second",
            {
                "create_state": "first",
                "build_state": "first",
                "test_mode": True,
                "update_requirements": False,
                "update_resources": False,
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            {
                "create_state": "first",
                "build_state": "first",
                "update_state": "second",
                "test_mode": True,
            },
        ),
    ]


def test_test_app_unbuilt(build_command, first_app_unbuilt, second_app):
    """Requesting a test build with update of an upbuilt app causes an update
    before build."""
    # Add two apps; use the "unbuilt" version of the first app.
    build_command.apps = {
        "first": first_app_unbuilt,
        "second": second_app,
    }

    # Configure command line options
    options = build_command.parse_options(["-u", "--test"])

    # Run the build command
    build_command(**options)

    # The right sequence of things will be done
    assert build_command.actions == [
        # Tools are verified
        ("verify",),
        # First App exists, but hasn't been built; it will be updated then built.
        (
            "update",
            "first",
            {
                "test_mode": True,
                "update_requirements": False,
                "update_resources": False,
            },
        ),
        # App tools are verified for first app
        ("verify-app-tools", "first"),
        (
            "build",
            "first",
            {"update_state": "first", "test_mode": True},
        ),
        # Second app has been built before; it will be built again.
        (
            "update",
            "second",
            {
                "update_state": "first",
                "build_state": "first",
                "test_mode": True,
                "update_requirements": False,
                "update_resources": False,
            },
        ),
        # App tools are verified for second app
        ("verify-app-tools", "second"),
        (
            "build",
            "second",
            {"update_state": "second", "build_state": "first", "test_mode": True},
        ),
    ]
